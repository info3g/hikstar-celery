-------------------------------------------------------------------------------
-- Evenements utilities
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION ft_troncon_interpolate(troncon integer, point geometry) RETURNS RECORD AS $$
DECLARE
  line GEOMETRY;
  result RECORD;
BEGIN
    SELECT shape_2d FROM hike_trailsection WHERE trailsection_id=troncon INTO line;
    SELECT * FROM ST_InterpolateAlong(line, point) AS (position FLOAT, distance FLOAT) INTO result;
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-------------------------------------------------------------------------------
-- Keep dates up-to-date
-------------------------------------------------------------------------------

DROP TRIGGER IF EXISTS hike_event_date_insert_tgr ON hike_event;
CREATE TRIGGER hike_event_date_insert_tgr
    BEFORE INSERT ON hike_event
    FOR EACH ROW EXECUTE PROCEDURE ft_date_insert();

DROP TRIGGER IF EXISTS hike_event_date_update_tgr ON hike_event;
CREATE TRIGGER hike_event_date_update_tgr
    BEFORE INSERT OR UPDATE ON hike_event
    FOR EACH ROW EXECUTE PROCEDURE ft_date_update();

---------------------------------------------------------------------
-- Make sure cache key (base on lastest updated) is refresh on DELETE
-- we implemented field "deleted" in our event table just as Geotrek
-- "deleted" is to decide whether an event should be shown or not
---------------------------------------------------------------------

DROP TRIGGER IF EXISTS hike_event_latest_updated_d_tgr ON hike_event;

CREATE OR REPLACE FUNCTION hike_event_latest_updated_d() RETURNS trigger AS $$
DECLARE
BEGIN
    UPDATE hike_event SET date_update = NOW()
    WHERE event_id IN (SELECT event_id FROM hike_event ORDER BY date_update DESC LIMIT 1);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER hike_event_latest_updated_d_tgr
AFTER DELETE ON hike_event
FOR EACH ROW EXECUTE PROCEDURE hike_event_latest_updated_d();

-------------------------------------------------------------------------------
-- Update geometry of an "event"
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION update_geometry_of_evenement(eid integer) RETURNS void AS $$
DECLARE
    egeom geometry;
    egeom_3d geometry;
    lines_only boolean;
    points_only boolean;
    position_point float;
    elevation elevation_infos;
    t_count integer;
    t_offset float;

    t_start float;
    t_end float;
    t_geom geometry;
    t_geom_3d geometry;
    tomerge geometry[];
    tomerge_3d geometry[];
BEGIN
    -- See what kind of trailsection we have
    SELECT bool_and(et.start_position != et.end_position), bool_and(et.start_position = et.end_position), count(*)
        INTO lines_only, points_only, t_count
        FROM hike_eventtrailsection et
        WHERE et.evnt = eid;
    -----------------------------------------------------------------------------
    -- Geotrek comments:
    -- /!\ linear offset (start and end point) are given as a fraction of the
    -- 2D-length in Postgis. Since we are working on 3D geometry, it could lead
    -- to unexpected results.
    -- January 2013 : It does indeed.

    -- RAISE NOTICE 'update_geometry_of_evenement (lines_only:% points_only:% t_count:%)', lines_only, points_only, t_count;
    -----------------------------------------------------------------------------

    IF t_count = 0 THEN
        -- No more trailsection, close this trailsection
        UPDATE hike_event SET deleted = true, shape_2d = NULL, lgth = 0 WHERE event_id = eid;
    ELSIF (NOT lines_only AND t_count = 1) OR points_only THEN
        -- Special case: the topology describe a point on the path
        -- Note: We are faking a M-geometry in order to use LocateAlong.
        -- This is handy because this function includes an offset parameter
        -- which could be otherwise diffcult to handle.
        SELECT shape_2d, e_offset INTO egeom, t_offset FROM hike_event e WHERE e.event_id = eid;

        -- RAISE NOTICE '% % % %', (t_offset = 0), (egeom IS NULL), (ST_IsEmpty(egeom)), (ST_X(egeom) = 0 AND ST_Y(egeom) = 0);
        -- ST_X/ST_Y Return the X/Y coordinate of the point
        
        IF t_offset = 0 OR egeom IS NULL OR ST_IsEmpty(egeom) OR (ST_X(egeom) = 0 AND ST_Y(egeom) = 0) THEN

        -- ST_LocateAlong can give no point when we try to get the startpoint or the endpoint of the line

            SELECT et.start_position INTO position_point FROM hike_eventtrailsection et WHERE et.evnt = eid;

            IF (position_point = 0) THEN
                SELECT ST_StartPoint(t.shape_2d) INTO egeom
                FROM hike_event e, hike_eventtrailsection et, hike_trailsection t
                WHERE e.event_id = eid AND et.evnt = e.event_id AND et.trailsection = t.trailsection_id;

            ELSIF (position_point = 1) THEN
                SELECT ST_EndPoint(t.shape_2d) INTO egeom
                FROM hike_event e, hike_eventtrailsection et, hike_trailsection t
                WHERE e.event_id = eid AND et.evnt = e.event_id AND et.trailsection = t.trailsection_id;

            ELSE
                SELECT ST_GeometryN(ST_LocateAlong(ST_AddMeasure(ST_Force2D(t.shape_2d), 0, 1), et.start_position, e.e_offset), 1)
                INTO egeom
                FROM hike_event e, hike_eventtrailsection et, hike_trailsection t
                WHERE e.event_id = eid AND et.evnt = e.event_id AND et.trailsection = t.trailsection_id;
            END IF;
        END IF;       

        egeom_3d := egeom;
    ELSE
        -- Regular case: the topology describe a line
        -- NOTE: LineMerge and Line_Substring work on X and Y only. If two
        -- points in the line have the same X/Y but a different Z, these
        -- functions will see only one point. --> No problem in mountain path management.
        FOR t_offset, t_geom, t_geom_3d IN SELECT e.e_offset, ST_Smart_Line_Substring(t.shape_2d, et.start_position, et.end_position),
                                                               ST_Smart_Line_Substring(t.shape, et.start_position, et.end_position)
               FROM hike_event e, hike_eventtrailsection et, hike_trailsection t
               WHERE e.event_id = eid AND et.evnt = e.event_id AND et.trailsection = t.trailsection_id
                 AND et.start_position != et.end_position
               ORDER BY et.order, et.eventtrailsection_id  -- /!\ We suppose that eventtrailsection were created in the right order
        LOOP
            tomerge := array_append(tomerge, t_geom);
            tomerge_3d := array_append(tomerge_3d, t_geom_3d);
        END LOOP;

        egeom := ft_Smart_MakeLine(tomerge);
        egeom_3d := ft_Smart_MakeLine(tomerge_3d);
        -- Add some offset if necessary.
        IF t_offset != 0 THEN
            egeom := ST_GeometryN(ST_LocateBetween(ST_AddMeasure(egeom, 0, 1), 0, 1, t_offset), 1);
            egeom_3d := ST_GeometryN(ST_LocateBetween(ST_AddMeasure(egeom_3d, 0, 1), 0, 1, t_offset), 1);
        END IF;
    END IF;

    IF t_count > 0 THEN
        SELECT * FROM ft_elevation_infos(egeom_3d, 1) INTO elevation;
        UPDATE hike_event SET shape_2d = ST_Force2D(egeom),
                                 shape = ST_Multi(ST_Force3DZ(elevation.draped)),
                                 lgth = ST_3DLength(ST_Transform(elevation.draped),32618),
                                 slope = elevation.slope,
                                 min_elevation = elevation.min_elevation,
                                 max_elevation = elevation.max_elevation,
                                 ascent = elevation.positive_gain,
                                 descent = elevation.negative_gain
                             WHERE event_id = eid;
    END IF;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION evenement_elevation_iu() RETURNS trigger AS $$
DECLARE
    elevation elevation_infos;
BEGIN
    -- 1 was {ALTIMETRIC_PROFILE_STEP} in Geotrek
    SELECT * FROM ft_elevation_infos(NEW.geom, 1) INTO elevation;
    -- Update path geometry
    NEW.shape := elevation.draped;
    NEW.lgth := ST_Length(ST_Force2D(ST_GeomFromEWKT(elevation.draped)),true);
    NEW.slope := elevation.slope;
    NEW.min_elevation := elevation.min_elevation;
    NEW.max_elevation := elevation.max_elevation;
    NEW.ascent := elevation.positive_gain;
    NEW.descent := elevation.negative_gain;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-------------------------------------------------------------------------------
-- Update geometry when offset change
-- We keep the codes here but for the moment Hikster do not need this yet
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION update_evenement_geom_when_offset_changes() RETURNS trigger AS $$
BEGIN
    -- Note: We are using an "after" trigger here because the function below
    -- takes topology id as an argument and emits its own SQL queries to read
    -- and write data.
    -- Since the evenement to be modified is available in NEW, we could improve
    -- performance with some refactoring.

    PERFORM update_geometry_of_evenement(NEW.event_id);

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS event_offset_u_tgr ON hike_event;
CREATE TRIGGER event_offset_u_tgr
AFTER UPDATE OF e_offset ON hike_event
FOR EACH ROW EXECUTE PROCEDURE update_evenement_geom_when_offset_changes();

-------------------------------------------------------------------------------
-- update the trail geometry when an event shape_2d gets updated
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION update_geometry_of_trail() RETURNS trigger AS $$

BEGIN
  UPDATE hike_trail SET
    shape_2d = hike_event.shape_2d,
    shape=ST_Multi(hike_event.shape),
    total_length = hike_event.lgth,
    height_positive = hike_event.ascent,
    height_negative = hike_event.descent,
    min_elevation = hike_event.min_elevation,
    max_elevation = hike_event.max_elevation,
    height_difference = hike_event.slope
    FROM hike_event WHERE hike_event.event_id = hike_trail.trail_id;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_geometry_of_trail_trg ON hike_event;
CREATE TRIGGER update_geometry_of_trail_trg
AFTER INSERT OR UPDATE OF shape_2d ON hike_event
FOR EACH ROW EXECUTE PROCEDURE update_geometry_of_trail();
