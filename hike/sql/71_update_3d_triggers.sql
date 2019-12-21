CREATE OR REPLACE FUNCTION ft_smooth_line(geom geometry)
  RETURNS SETOF geometry AS $$
  DECLARE
  current geometry;
  points3d geometry[];
  ele integer;
  last_ele integer;
  last_last_ele integer;
BEGIN
  points3d := ARRAY[]::geometry[];
  ele := NULL;
  last_ele := NULL;
  last_last_ele := NULL;

  FOR current IN SELECT (ST_DumpPoints(ST_Force3D(geom))).geom AS geom LOOP

    -- smoothing with last element
    ele := (ST_Z(current)::integer + coalesce(last_ele, ST_Z(current)::integer)) / 2;
    points3d := array_append(points3d, ST_MakePoint(ST_X(current), ST_Y(current), ele));

	  last_last_ele := last_ele;
	  last_ele := ele;

  END LOOP;

  RETURN QUERY SELECT (ST_DumpPoints(ST_SetSRID(ST_MakeLine(points3d), ST_SRID(geom)))).geom as geom;

END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION ft_smooth_line(
    linegeom geometry,
    step integer)
  RETURNS SETOF geometry AS $$
-- function moving average on altitude lines with specified step

DECLARE

    points geometry[];
    points_output geometry[];
    current_values float;
    count_values integer;
    val geometry;
    element geometry;

BEGIN
    IF step <= 0
    THEN
        RETURN QUERY SELECT * FROM ft_smooth_line(linegeom);
    END IF;

    FOR element in SELECT (ST_DumpPoints(linegeom)).geom LOOP
		points := array_append(points, element);
    END LOOP;

    FOR i IN 0 .. array_length(points, 1) LOOP

        current_values := 0.0;
        count_values := 0;

        FOREACH val in ARRAY points[i-step:i+step] LOOP
          -- val is null when out of array
          IF val IS NOT NULL
          THEN
            count_values := count_values + 1;
            current_values := current_values + ST_Z(val);
          END IF;
        END LOOP;

        points_output := array_append(points_output, ST_MAKEPOINT(ST_X(points[i]), ST_Y(points[i]), (current_values / count_values)::integer));
    END LOOP;
    --RAISE EXCEPTION 'Nonexistent ID --> %', ST_ASEWKT(ST_SetSRID(ST_MakeLine(points_output), ST_SRID(linegeom)));
    RETURN QUERY SELECT (ST_DumpPoints(ST_SetSRID(ST_MakeLine(points_output), ST_SRID(linegeom)))).geom as geom;

END;
$$ LANGUAGE plpgsql;
CREATE OR REPLACE FUNCTION add_point_elevation(geom geometry) RETURNS geometry AS $$
  DECLARE
  ele integer;
  geom3d geometry;
BEGIN
  ele := coalesce(ST_Z(geom)::integer, 0);
  IF ele > 0 THEN
    RETURN geom;
  END IF;

  -- Ensure we have a DEM
  PERFORM * FROM raster_columns WHERE r_table_name = 'mnt';
  IF FOUND THEN
    SELECT ST_Value(rast, 1, geom)::integer INTO ele
    FROM mnt
    WHERE ST_Intersects(rast, geom);
    IF NOT FOUND THEN
      ele := 0;
    END IF;
  END IF;

  geom3d := ST_MakePoint(ST_X(geom), ST_Y(geom), ele);
  geom3d := ST_SetSRID(geom3d, ST_SRID(geom));
  RETURN geom3d;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION ft_elevation_infos(geom geometry, epsilon float) RETURNS elevation_infos AS $$
DECLARE
    num_points integer;
    current geometry;
    points3d geometry[];
    points3d_smoothed geometry[];
    points3d_simplified geometry[];
    result elevation_infos;
    previous_geom geometry;
    line geometry;
BEGIN
    -- Skip if no DEM (speed-up tests)
    PERFORM * FROM raster_columns WHERE r_table_name = 'mnt';
    IF NOT FOUND THEN
        SELECT ST_Force3DZ(geom), 0.0, 0, 0, 0, 0 INTO result;
        RETURN result;
    END IF;

    -- Ensure parameter is a point or a line
    IF ST_GeometryType(geom) NOT IN ('ST_Point', 'ST_LineString') THEN
        SELECT ST_Force3DZ(geom), 0.0, 0, 0, 0, 0 INTO result;
        RETURN result;
    END IF;

    -- Specific case for points
    IF ST_GeometryType(geom) = 'ST_Point' THEN
        current := add_point_elevation(geom);
        SELECT current, 0.0, ST_Z(current), ST_Z(current), 0, 0 INTO result;
        RETURN result;
    END IF;

    -- Case of epsilon <= 0:
    IF epsilon <= 0
    THEN
        SELECT * FROM ft_elevation_infos(geom) INTO result;
        RETURN result;
    END IF;

    -- Now geom is LineString only.

    result.positive_gain := 0;
    result.negative_gain := 0;
    points3d := ARRAY[]::geometry[];
    points3d_smoothed := ARRAY[]::geometry[];
    points3d_simplified := ARRAY[]::geometry[];

    -- geotrek setting {{ALTIMETRIC_PROFILE_PRECISION}} is 25 in meters sampling precision
    FOR current IN SELECT * FROM ft_drape_line(geom, 1) LOOP
        -- Create the 3d points
        points3d := array_append(points3d, current);
    END LOOP;

    -- line := St_MakeLine(points3d);
    -- RAISE NOTICE 'line_before_smoothed %', ST_AsText(line);

    -- smoothing line
    FOR current IN SELECT * FROM ft_smooth_line(St_MakeLine(points3d), 1) LOOP
        -- Create the 3d points
        points3d_smoothed := array_append(points3d_smoothed, current);
    END LOOP;

    -- line := St_MakeLine(points3d_smoothed);
    -- RAISE NOTICE 'smoothed %', ST_AsText(line);

    -- simplify gain calculs
    previous_geom := NULL;

    -- Compute gain using simplification
    -- see http://www.postgis.org/docs/ST_Simplify.html
    --     https://en.wikipedia.org/wiki/Ramer%E2%80%93Douglas%E2%80%93Peucker_algorithm
    --FOR current IN SELECT (ST_DUMPPOINTS(ST_SIMPLIFYPRESERVETOPOLOGY(ST_MAKELINE(points3d_smoothed), epsilon))).geom LOOP
    FOR current IN SELECT (ST_DumpPoints(ST_MakeLine(points3d_smoothed))).geom LOOP
        -- Add positive only if current - previous_geom > 0
        result.positive_gain := result.positive_gain + greatest(ST_Z(current) - coalesce(ST_Z(previous_geom), ST_Z(current)), 0);
      -- Add negative only if current - previous_geom < 0
        result.negative_gain := result.negative_gain + least(ST_Z(current) - coalesce(ST_Z(previous_geom), ST_Z(current)), 0);
        previous_geom := current;
    END LOOP;

    result.draped := ST_SetSRID(ST_MakeLine(points3d_smoothed), ST_SRID(geom));

    -- Compute elevation using (higher resolution)
    result.min_elevation := ST_ZMin(result.draped)::integer;
    result.max_elevation := ST_ZMax(result.draped)::integer;

    -- Compute slope
    result.slope := 0.0;

    IF ST_Length(ST_GeomFromEWKT(geom),true) > 0 THEN
      result.slope := (result.max_elevation - result.min_elevation) / ST_Length(ST_GeomFromEWKT(geom),true);
    END IF;

    -- RAISE NOTICE 'min_elevation %', result.min_elevation;       -- either this
    -- RAISE NOTICE 'max_elevation %', result.max_elevation;       -- either this
    -- RAISE NOTICE 'slope %', result.slope;       -- either this
    -- RAISE NOTICE 'draped %', ST_AsText(result.draped);

    RETURN result;
END;
$$ LANGUAGE plpgsql;


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
        FOR t_offset, t_geom, t_geom_3d IN SELECT e.e_offset, ST_Smart_Line_Substring(t.shape_2d, et.start_position, et.end_position), ST_Smart_Line_Substring(t.shape, et.start_position, et.end_position)
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

    -- RAISE NOTICE 'egeom_3d %', ST_AsText(egeom_3d);

    IF t_count > 0 THEN
        -- We put back 3D calculation into trigger to have real time result
        SELECT * FROM ft_elevation_infos(egeom_3d, 1) INTO elevation;
        -- RAISE NOTICE 'draped %', ST_AsText(elevation.draped);
        UPDATE hike_event SET shape_2d = ST_Force2D(egeom),
                              shape = ST_Force3DZ(elevation.draped),
                              lgth = ST_Length(ST_Force2D(ST_GeomFromEWKT(elevation.draped)),true),
                              slope = elevation.slope,
                              min_elevation = elevation.min_elevation,
                              max_elevation = elevation.max_elevation,
                              ascent = elevation.positive_gain,
                              descent = elevation.negative_gain
                             WHERE event_id = eid;
    END IF;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION hikster_trailsection_shape_force3d() RETURNS trigger AS $$
  DECLARE
  elevation elevation_infos;

BEGIN
  SELECT * FROM ft_elevation_infos(NEW.shape_2d, 1) INTO elevation;
  -- Update path geometry
  NEW.shape := elevation.draped;
  NEW.lgth := ST_Length(ST_Force2D(ST_GeomFromEWKT(elevation.draped)),true);
  NEW.slope := elevation.slope;
  NEW.min_elevation:= elevation.min_elevation;
  NEW.max_elevation:= elevation.max_elevation;
  NEW.ascent:= elevation.positive_gain;
  NEW.descent:= elevation.negative_gain;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS hikster_new_trailsection_shape_force3dtrg ON hike_trailsection;
CREATE TRIGGER hikster_new_trailsection_shape_force3dtrg
  BEFORE INSERT OR UPDATE OF shape_2d ON hike_trailsection
  FOR EACH ROW EXECUTE PROCEDURE hikster_trailsection_shape_force3d();


CREATE OR REPLACE FUNCTION update_geometry_of_trail() RETURNS trigger AS $$

BEGIN
  UPDATE hike_trail SET
    shape_2d = NEW.shape_2d,
    shape = ST_Multi(NEW.shape),
    total_length = NEW.lgth,
    height_positive = NEW.ascent,
    height_negative = NEW.descent,
    min_elevation = NEW.min_elevation,
    max_elevation = NEW.max_elevation,
    height_difference = NEW.slope
    WHERE trail_id = NEW.event_id;
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_geometry_of_trail_trg ON hike_event;
CREATE TRIGGER update_geometry_of_trail_trg
  AFTER INSERT OR UPDATE OF shape ON hike_event
  FOR EACH ROW EXECUTE PROCEDURE update_geometry_of_trail();

DROP TRIGGER IF EXISTS hike_eventtrailsection_geometry_tgr ON hike_eventtrailsection;
CREATE TRIGGER hike_eventtrailsection_geometry_tgr
AFTER INSERT OR UPDATE ON hike_eventtrailsection
FOR EACH ROW EXECUTE PROCEDURE hike_eventtrailsection_geometry();
