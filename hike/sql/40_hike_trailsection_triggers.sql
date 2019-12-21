--------------------------------------------------------------------------
-- Force Default values to trailsction insertion
--------------------------------------------------------------------------
ALTER TABLE hike_trailsection ALTER COLUMN date_insert SET DEFAULT now();
ALTER TABLE hike_trailsection ALTER COLUMN date_update SET DEFAULT now();
ALTER TABLE hike_trailsection ALTER COLUMN "valid" SET DEFAULT true;
ALTER TABLE hike_trailsection ALTER COLUMN visible SET DEFAULT true;


--------------------------------------------------------------------------
-- Keep dates up-to-date
-------------------------------------------------------------------------------

DROP TRIGGER IF EXISTS hike_trailsection_date_insert_tgr ON hike_trailsection;
CREATE TRIGGER hike_trailsection_date_insert_tgr
    BEFORE INSERT ON hike_trailsection
    FOR EACH ROW EXECUTE PROCEDURE ft_date_insert();

DROP TRIGGER IF EXISTS hike_trailsection_date_update_tgr ON hike_trailsection;
CREATE TRIGGER hike_trailsection_date_update_tgr
    BEFORE INSERT OR UPDATE ON hike_trailsection
    FOR EACH ROW EXECUTE PROCEDURE ft_date_update();

-------------------------------------------------------------------------------
-- Update geometry of related topologies
-------------------------------------------------------------------------------

DROP TRIGGER IF EXISTS hike_eventtrailsection_geom_u_tgr ON hike_trailsection;
DROP TRIGGER IF EXISTS hike_trailsection_90_evenements_geom_u_tgr ON hike_trailsection;

CREATE OR REPLACE FUNCTION update_evenement_geom_when_troncon_changes() RETURNS trigger AS $$
DECLARE
    eid integer;
    egeom geometry;
    linear_offset float;
    side_offset float;
BEGIN
    -- Geometry of linear topologies are always updated
    -- Geometry of point topologies are updated if offset = 0
    FOR eid IN SELECT e.event_id
               FROM hike_eventtrailsection et, hike_event e
               WHERE et.trailsection = NEW.trailsection_id AND et.evnt = e.event_id
               GROUP BY e.event_id, e.e_offset
               HAVING BOOL_OR(et.start_position != et.end_position) OR e.e_offset = 0.0
    LOOP
        PERFORM update_geometry_of_evenement(eid);
    END LOOP;

    -- Special case of point geometries with offset != 0
    FOR eid, egeom IN SELECT e.event_id, e.shape_2d
               FROM hike_eventtrailsection et, hike_event e
               WHERE et.trailsection = NEW.trailsection_id AND et.evnt = e.event_id
               GROUP BY e.event_id, e.e_offset
               HAVING COUNT(et.eventtrailsection_id) = 1 AND BOOL_OR(et.start_position = et.end_position) AND e.e_offset != 0.0
    LOOP
        SELECT * INTO linear_offset, side_offset FROM ST_InterpolateAlong(NEW.shape_2d, egeom) AS (position float, distance float);
        UPDATE hike_event SET e_offset = side_offset WHERE id = eid;
        UPDATE hike_eventtrailsection SET start_position = linear_offset, end_position = linear_offset WHERE evnt = eid AND trailsection = NEW.trailsection_id;
    END LOOP;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER hike_trailsection_90_evenements_geom_u_tgr
AFTER UPDATE OF shape_2d ON hike_trailsection
FOR EACH ROW EXECUTE PROCEDURE update_evenement_geom_when_troncon_changes();

-------------------------------------------------------------------------------
-- Ensure paths have valid geometries
-------------------------------------------------------------------------------

-- ALTER TABLE hike_trailsection DROP CONSTRAINT IF EXISTS troncons_geom_issimple;

-- ALTER TABLE hike_trailsection DROP CONSTRAINT IF EXISTS l_t_troncon_geom_isvalid;
-- ALTER TABLE hike_trailsection ADD CONSTRAINT l_t_troncon_geom_isvalid CHECK (ST_IsValid(shape_2d));

-- ALTER TABLE hike_trailsection DROP CONSTRAINT IF EXISTS l_t_troncon_geom_issimple;
-- ALTER TABLE hike_trailsection ADD CONSTRAINT l_t_troncon_geom_issimple CHECK (ST_IsSimple(shape_2d));


---------------------------------------------------------------------
-- Make sure cache key (base on latest updated) is refresh on DELETE
---------------------------------------------------------------------

DROP TRIGGER IF EXISTS hike_trailsection_latest_updated_d_tgr ON hike_trailsection;

CREATE OR REPLACE FUNCTION trailsection_latest_updated_d() RETURNS trigger AS $$
DECLARE
BEGIN
    -- Touch latest path
    UPDATE hike_trailsection SET date_update = NOW()
    WHERE trailsection_id IN (SELECT trailsection_id FROM hike_trailsection ORDER BY date_update DESC LIMIT 1);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER hike_trailsection_latest_updated_d_tgr
AFTER DELETE ON hike_trailsection
FOR EACH ROW EXECUTE PROCEDURE trailsection_latest_updated_d();

---------------------------------------------------------------------
-- trailsection split function
---------------------------------------------------------------------

DROP TRIGGER IF EXISTS hike_trailsection_00_snap_geom_iu_tgr ON hike_trailsection;

CREATE OR REPLACE FUNCTION trailsections_snap_extremities() RETURNS trigger AS $$
DECLARE
    linestart geometry;
    lineend geometry;
    other geometry;
    closest geometry;
    result geometry;
    newline geometry[];
    d float8;

    DISTANCE float8;
BEGIN
	-- Geotrek has a PATH_SNAPPING_DISTANCE setting equals to 1
    DISTANCE := 0.00002;

    linestart := ST_StartPoint(NEW.shape_2d);
    lineend := ST_EndPoint(NEW.shape_2d);

    closest := NULL;
    SELECT ST_ClosestPoint(shape_2d, linestart), shape_2d INTO closest, other
      FROM hike_trailsection
      WHERE shape_2d && ST_Buffer(NEW.shape_2d, DISTANCE * 2)
        AND trailsection_id != NEW.trailsection_id
        AND ST_Distance(shape_2d, linestart) < DISTANCE
      ORDER BY ST_Distance(shape_2d, linestart)
      LIMIT 1;

    IF closest IS NULL THEN
        result := linestart;
    ELSE
        result := closest;
        d := DISTANCE;
        FOR i IN 1..ST_NPoints(other) LOOP
            IF ST_Distance(closest, ST_PointN(other, i)) < DISTANCE AND ST_Distance(closest, ST_PointN(other, i)) < d THEN
                d := ST_Distance(closest, ST_PointN(other, i));
                result := ST_PointN(other, i);
            END IF;
        END LOOP;
        IF NOT ST_Equals(linestart, result) THEN
            RAISE NOTICE 'Snapped start % to %, from %', ST_AsText(linestart), ST_AsText(result), ST_AsText(other);
        END IF;
    END IF;
    newline := array_append(newline, result);

    FOR i IN 2..ST_NPoints(NEW.shape_2d)-1 LOOP
        newline := array_append(newline, ST_PointN(NEW.shape_2d, i));
    END LOOP;

    closest := NULL;
    SELECT ST_ClosestPoint(shape_2d, lineend), shape_2d INTO closest, other

      FROM hike_trailsection
      WHERE shape_2d && ST_Buffer(NEW.shape_2d, DISTANCE * 2)
        AND trailsection_id != NEW.trailsection_id
        AND ST_Distance(shape_2d, lineend) < DISTANCE
      ORDER BY ST_Distance(shape_2d, lineend)
      LIMIT 1;
    IF closest IS NULL THEN
        result := lineend;
    ELSE
        result := closest;
        d := DISTANCE;
        FOR i IN 1..ST_NPoints(other) LOOP
            IF ST_Distance(closest, ST_PointN(other, i)) < DISTANCE AND ST_Distance(closest, ST_PointN(other, i)) < d THEN
                d := ST_Distance(closest, ST_PointN(other, i));
                result := ST_PointN(other, i);
            END IF;
        END LOOP;
        IF NOT ST_Equals(lineend, result) THEN
            RAISE NOTICE 'Snapped end % to %, from %', ST_AsText(lineend), ST_AsText(result), ST_AsText(other);
        END IF;
    END IF;
    newline := array_append(newline, result);

    RAISE NOTICE 'New geom %', ST_AsText(ST_MakeLine(newline));
    NEW.shape_2d := ST_MakeLine(newline);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER hike_trailsection_00_snap_geom_iu_tgr
BEFORE INSERT OR UPDATE OF shape_2d ON hike_trailsection
FOR EACH ROW EXECUTE PROCEDURE trailsections_snap_extremities();

-------------------------------------------------------------------------------
-- Split paths when crossing each other
-------------------------------------------------------------------------------

DROP TRIGGER IF EXISTS hike_trailsection_split_geom_iu_tgr ON hike_trailsection;
DROP TRIGGER IF EXISTS hike_trailsection_10_split_geom_iu_tgr ON hike_trailsection;

CREATE OR REPLACE FUNCTION hike_trailsection_event_intersect_split() RETURNS trigger AS $$
DECLARE
    troncon record;
    activity record;
    tid_clone integer;
    t_count integer;
    existing_et integer[];
    t_geom geometry;

    fraction float8;
    a float8;
    b float8;
    segment geometry;
    newgeom geometry;

    intersections_on_new float8[];
    intersections_on_current float8[];
BEGIN

    -- Copy original geometry
    newgeom := NEW.shape_2d;
    intersections_on_new := ARRAY[0::float];

    -- Iterate paths intersecting, excluding those touching only by extremities
    FOR troncon IN SELECT *
                   FROM hike_trailsection t
                   WHERE trailsection_id != NEW.trailsection_id
                         AND ST_DWITHIN(t.shape_2d, NEW.shape_2d, 0)
                         AND GeometryType(ST_Intersection(shape_2d, NEW.shape_2d)) IN ('POINT', 'MULTIPOINT')
    LOOP

        RAISE NOTICE '%-% (%) intersects %-% (%) : %', NEW.shape_2d, NEW.name, ST_AsText(NEW.shape_2d), troncon.trailsection_id, troncon.name, ST_AsText(troncon.shape_2d), ST_AsText(ST_Intersection(troncon.shape_2d, NEW.shape_2d));

        -- Locate intersecting point(s) on NEW, for later use
        FOR fraction IN SELECT ST_LineLocatePoint(NEW.shape_2d,
                                                    (ST_Dump(ST_Intersection(troncon.shape_2d, NEW.shape_2d))).geom)
                        WHERE NOT ST_EQUALS(ST_STARTPOINT(NEW.shape_2d), ST_STARTPOINT(troncon.shape_2d))
                          AND NOT ST_EQUALS(ST_STARTPOINT(NEW.shape_2d), ST_ENDPOINT(troncon.shape_2d))
                          AND NOT ST_EQUALS(ST_ENDPOINT(NEW.shape_2d), ST_STARTPOINT(troncon.shape_2d))
                          AND NOT ST_EQUALS(ST_ENDPOINT(NEW.shape_2d), ST_ENDPOINT(troncon.shape_2d))
        LOOP
            intersections_on_new := array_append(intersections_on_new, fraction);
        END LOOP;
        intersections_on_new := array_append(intersections_on_new, 1::float);

        -- Sort intersection points and remove duplicates (0 and 1 can appear twice)
        SELECT array_agg(sub.fraction) INTO intersections_on_new
            FROM (SELECT DISTINCT unnest(intersections_on_new) AS fraction ORDER BY fraction) AS sub;

        -- Locate intersecting point(s) on current path (array of  : {0, 0.32, 0.89, 1})
        intersections_on_current := ARRAY[0::float];
        FOR fraction IN SELECT ST_LineLocatePoint(troncon.shape_2d, (ST_Dump(ST_Intersection(troncon.shape_2d, NEW.shape_2d))).geom)
        LOOP
            intersections_on_current := array_append(intersections_on_current, fraction);
        END LOOP;
        intersections_on_current := array_append(intersections_on_current, 1::float);

        -- Sort intersection points and remove duplicates (0 and 1 can appear twice)
        SELECT array_agg(sub.fraction) INTO intersections_on_current
            FROM (SELECT DISTINCT unnest(intersections_on_current) AS fraction ORDER BY fraction) AS sub;

        IF array_length(intersections_on_new, 1) > 2 AND array_length(intersections_on_current, 1) > 2 THEN
            -- If both intersects, one is enough, since split trigger will be applied recursively.
            intersections_on_new := ARRAY[]::float[];
        END IF;

    --------------------------------------------------------------------
    -- 1. Handle NEW intersecting with existing paths
    --------------------------------------------------------------------
        -- Skip if intersections are 0,1 (means not crossing)
        IF array_length(intersections_on_new, 1) > 2 THEN
            RAISE NOTICE 'New: % % intersecting on NEW % % : %', NEW.trailsection_id, NEW.name, troncon.trailsection_id, troncon.name, intersections_on_new;

            FOR i IN 1..(array_length(intersections_on_new, 1) - 1)
            LOOP
                a := intersections_on_new[i];
                b := intersections_on_new[i+1];

                segment := ST_LineSubstring(newgeom, a, b);

                IF coalesce(ST_Length(segment,true), 0) < 2 THEN
                     intersections_on_new[i+1] := a;
                     CONTINUE;
                END IF;
                IF i = 1 THEN
                    -- First segment : shrink it !
                    SELECT COUNT(*) INTO t_count FROM hike_trailsection WHERE name = NEW.name AND ST_Equals(shape_2d, segment);
                    IF t_count = 0 THEN
                        RAISE NOTICE 'New: Skrink %-% (%) to %', NEW.trailsection_id, NEW.name, ST_AsText(NEW.shape_2d), ST_AsText(segment);
                        UPDATE hike_trailsection SET shape_2d = segment WHERE trailsection_id = NEW.trailsection_id;
                    END IF;
                ELSE
                    -- Next ones : create clones !
                    SELECT COUNT(*) INTO t_count FROM hike_trailsection WHERE name = NEW.name AND ST_Equals(shape_2d, segment);
                    IF t_count = 0 THEN
                        RAISE NOTICE 'New: Create clone of %-% with geom %', NEW.trailsection_id, NEW.name, ST_AsText(segment);
                        INSERT INTO hike_trailsection (visible,
                                                 "valid",
                                                 "name",
                                                 "comments",
                                                 departure,
                                                 arrival,
                                                 difficulty,
                                                 external_id,
                                                 shape_2d)
                            VALUES (NEW.visible,
                                    NEW.valid,
                                    NEW.name,
                                    NEW.comments,
                                    NEW.departure,
                                    NEW.arrival,
                                    NEW.difficulty,
                                    NEW.external_id,
                                    segment)
                            RETURNING trailsection_id INTO tid_clone;
                    END IF;
                END IF;
            END LOOP;

            -- Recursive triggers did all the work. Stop here.
            RETURN NULL;
        END IF;


    --------------------------------------------------------------------
    -- 2. Handle paths intersecting with NEW
    --------------------------------------------------------------------
        -- Skip if intersections are 0,1 (means not crossing)
        IF array_length(intersections_on_current, 1) > 2 THEN
            RAISE NOTICE 'Current: % % intersecting on current % % : %', NEW.trailsection_id, NEW.name, troncon.trailsection_id, troncon.name, intersections_on_current;

            SELECT array_agg(trailsection) INTO existing_et FROM hike_eventtrailsection et WHERE et.trailsection = troncon.trailsection_id;
             IF existing_et IS NOT NULL THEN
                 RAISE NOTICE 'Existing topologies id for %-% (%): %', troncon.trailsection_id, troncon.name, ST_AsText(troncon.shape_2d), existing_et;
             END IF;

            FOR i IN 1..(array_length(intersections_on_current, 1) - 1)
            LOOP
                a := intersections_on_current[i];
                b := intersections_on_current[i+1];

                segment := ST_LineSubstring(troncon.shape_2d, a, b);

                IF coalesce(ST_Length(segment,true), 0) < 2 THEN
                     intersections_on_new[i+1] := a;
                     CONTINUE;
                END IF;

                IF i = 1 THEN
                    -- First segment : shrink it !
                    SELECT shape_2d INTO t_geom FROM hike_trailsection WHERE trailsection_id = troncon.trailsection_id;
                    IF NOT ST_Equals(t_geom, segment) THEN
                        RAISE NOTICE 'Current: Skrink %-% (%) to %', troncon.trailsection_id, troncon.name, ST_AsText(troncon.shape_2d), ST_AsText(segment);
                        UPDATE hike_trailsection SET shape_2d = segment WHERE trailsection_id = troncon.trailsection_id;
                    END IF;
                ELSE
                    -- Next ones : create clones !
                    SELECT COUNT(*) INTO t_count FROM hike_trailsection WHERE ST_Equals(shape_2d, segment);
                    IF t_count = 0 THEN
                        RAISE NOTICE 'Current: Create clone of %-% (%) with geom %', troncon.trailsection_id, troncon.name, ST_AsText(troncon.shape_2d), ST_AsText(segment);
                        INSERT INTO hike_trailsection (visible,
                                                 "valid",
                                                 "name",
                                                 "comments",
                                                 departure,
                                                 arrival,
                                                 difficulty,
                                                 external_id,
                                                 shape_2d)
                            VALUES (troncon.visible,
                                    troncon.valid,
                                    troncon.name,
                                    troncon.comments,
                                    troncon.departure,
                                    troncon.arrival,
                                    troncon.difficulty,
                                    troncon.external_id,
                                    segment)
                            RETURNING trailsection_id INTO tid_clone;

                        -- Check if troncon is in the new segment
                        IF ST_Distance(newgeom, segment) = 0 THEN
                            IF troncon.trailsection_activities_uuid IS NOT NULL THEN
                                FOR activity IN SELECT * FROM hike_trailsectionactivities ta WHERE ta.trailsection_uuid = troncon.trailsection_activities_uuid LOOP
                                    RAISE NOTICE 'Inserted activity : % - %', tid_clone, activity.activity_id;
                                    INSERT INTO hike_trailsection_activity(trailsection_id, activity_id) VALUES(tid_clone, activity.activity_id);
                                END LOOP;
                            ELSE
                                FOR activity in SELECT * FROM hike_trailsection_activity ta WHERE ta.trailsection_id = troncon.trailsection_id LOOP
                                    RAISE NOTICE 'Inserted activity : % - %', tid_clone, activity.activity_id;
                                    INSERT INTO hike_trailsection_activity(trailsection_id, activity_id) VALUES(tid_clone, activity.activity_id);
                                END LOOP;
                            END IF;
                        END IF;

                        RAISE NOTICE 'Current: created clone id : % - %', tid_clone, NEW.trailsection_id;

						/*we don't have the following tables
                        -- Copy N-N relations
                        INSERT INTO l_r_troncon_reseau (path_id, network_id)
                            SELECT tid_clone, tr.network_id
                            FROM l_r_troncon_reseau tr
                            WHERE tr.path_id = troncon.id;
                        INSERT INTO l_r_troncon_usage (path_id, usage_id)
                            SELECT tid_clone, tr.usage_id
                            FROM l_r_troncon_usage tr
                            WHERE tr.path_id = troncon.id;
						*/

                        -- Copy topologies overlapping start/end
                        INSERT INTO hike_eventtrailsection (trailsection, evnt, start_position, end_position, "order")
                            SELECT
                                tid_clone,
                                et.evnt,
                                CASE WHEN start_position <= end_position THEN
                                    (greatest(a, start_position) - a) / (b - a)
                                ELSE
                                    (least(b, start_position) - a) / (b - a)
                                END,
                                CASE WHEN start_position <= end_position THEN
                                    (least(b, end_position) - a) / (b - a)
                                ELSE
                                    (greatest(a, end_position) - a) / (b - a)
                                END,
                                et.order
                            FROM hike_eventtrailsection et,
                                 hike_event e
                            WHERE et.evnt = e.event_id
                                  AND et.trailsection = troncon.trailsection_id
                                  AND ((least(start_position, end_position) < b AND greatest(start_position, end_position) > a) OR       -- Overlapping
                                       (start_position = end_position AND start_position = a AND e_offset = 0)); -- Point
                        GET DIAGNOSTICS t_count = ROW_COUNT;
                        IF t_count > 0 THEN
                            RAISE NOTICE 'Duplicated % topologies of %-% (%) on [% ; %] for %-% (%)', t_count, troncon.trailsection_id, troncon.name, ST_AsText(troncon.shape_2d), a, b, tid_clone, troncon.name, ST_AsText(segment);
                        END IF;
                        -- Special case : point topology at the end of path
                        IF b = 1 THEN
                            SELECT shape_2d INTO t_geom FROM hike_trailsection WHERE trailsection_id = troncon.trailsection_id;
                            fraction := ST_LineLocatePoint(segment, ST_EndPoint(troncon.shape_2d));
                            INSERT INTO hike_eventtrailsection (trailsection, evnt, start_position, end_position)
                                SELECT tid_clone, evnt, start_position, end_position
                                FROM hike_eventtrailsection et,
                                     hike_event e
                                WHERE et.evnt = e.event_id AND
                                      et.trailsection = troncon.trailsection_id AND
                                      start_position = end_position AND
                                      start_position = 1 AND
                                      e_offset = 0;
                            GET DIAGNOSTICS t_count = ROW_COUNT;
                            IF t_count > 0 THEN
                                RAISE NOTICE 'Duplicated % point topologies of %-% (%) on intersection at the end of %-% (%) at [%]', t_count, troncon.trailsection_id, troncon.name, ST_AsText(t_geom), tid_clone, troncon.name, ST_AsText(segment), fraction;
                            END IF;
                        END IF;
                        -- Special case : point topology exactly where NEW path intersects
                        IF a > 0 THEN
                            fraction := ST_LineLocatePoint(NEW.shape_2d, ST_LineInterpolatePoint(troncon.shape_2d, a));
                            INSERT INTO hike_eventtrailsection (trailsection, evnt, start_position, end_position, "order")
                                SELECT NEW.trailsection_id, et.evnt, fraction, fraction, "order"
                                FROM hike_eventtrailsection et,
                                     hike_event e
                                WHERE et.evnt = e.event_id
                                  AND et.trailsection = troncon.trailsection_id
                                  AND start_position = end_position AND start_position = a
                                  AND e_offset = 0;
                            GET DIAGNOSTICS t_count = ROW_COUNT;
                            IF t_count > 0 THEN
                                RAISE NOTICE 'Duplicated % point topologies of %-% (%) on intersection by %-% (%) at [%]', t_count, troncon.trailsection_id, troncon.name, ST_AsText(troncon.shape_2d), NEW.trailsection_id, NEW.name, ST_AsText(NEW.shape_2d), a;
                            END IF;
                        END IF;
                    END IF;
                END IF;
            END LOOP;


            -- For each existing point topology with offset, re-attach it
            -- to the closest path, among those splitted.
            WITH existing_rec AS (SELECT MAX(et.eventtrailsection_id) AS eventtrailsection_id, e.e_offset, e.shape_2d
                                    FROM hike_eventtrailsection et,
                                         hike_event e
                                   WHERE et.evnt = e.event_id
                                     AND e.e_offset > 0
                                     AND et.trailsection = troncon.trailsection_id
                                     AND et.eventtrailsection_id = ANY(existing_et)
                                     GROUP BY e.event_id
                                     HAVING COUNT(et.eventtrailsection_id) = 1 AND BOOL_OR(et.start_position = et.end_position)),
                 closest_path AS (SELECT er.eventtrailsection_id AS et_id, t.trailsection_id AS closest_id
                                    FROM hike_trailsection t, existing_rec er
                                   WHERE t.trailsection_id != troncon.trailsection_id
                                     AND ST_Distance(er.shape_2d, t.shape_2d) < er.e_offset
                                ORDER BY ST_Distance(er.shape_2d, t.shape_2d)
                                   LIMIT 1)
                UPDATE hike_eventtrailsection SET trailsection = closest_id
                  FROM closest_path
                 WHERE eventtrailsection_id = et_id;
            GET DIAGNOSTICS t_count = ROW_COUNT;
            IF t_count > 0 THEN
                -- Update geom of affected paths to trigger update_evenement_geom_when_troncon_changes()
                UPDATE hike_trailsection t SET shape_2d = shape_2d
                  FROM hike_eventtrailsection et
                 WHERE t.trailsection_id = et.trailsection
                   AND et.start_position = et.end_position
                   AND et.eventtrailsection_id = ANY(existing_et);
            END IF;

            -- Update point topologies at intersection
            -- Trigger e_r_evenement_troncon_junction_point_iu_tgr
            UPDATE hike_eventtrailsection et SET start_position = start_position
             WHERE et.trailsection = NEW.trailsection_id
               AND start_position = end_position;

            -- Now handle first path topologies
            a := intersections_on_current[1];
            b := intersections_on_current[2];
            DELETE FROM hike_eventtrailsection et WHERE et.trailsection = troncon.trailsection_id
                                                 AND eventtrailsection_id = ANY(existing_et)
                                                 AND (least(start_position, end_position) > b OR greatest(start_position, end_position) < a);
            GET DIAGNOSTICS t_count = ROW_COUNT;
            IF t_count > 0 THEN
                RAISE NOTICE 'Removed % topologies of %-% on [% ; %]', t_count, troncon.trailsection_id,  troncon.name, a, b;
            END IF;

            -- Update topologies overlapping
            UPDATE hike_eventtrailsection et SET
                start_position = CASE WHEN start_position / (b - a) > 1 THEN 1 ELSE start_position / (b - a) END,
                end_position = CASE WHEN end_position / (b - a) > 1 THEN 1 ELSE end_position / (b - a) END
                WHERE et.trailsection = troncon.trailsection_id
                AND least(start_position, end_position) <= b AND greatest(start_position, end_position) >= a;
            GET DIAGNOSTICS t_count = ROW_COUNT;
            IF t_count > 0 THEN
                RAISE NOTICE 'Updated % topologies of %-% on [% ; %]', t_count, troncon.trailsection_id,  troncon.name, a, b;
            END IF;
        END IF;


    END LOOP;

    IF array_length(intersections_on_new, 1) > 0 OR array_length(intersections_on_current, 1) > 0 THEN
        RAISE NOTICE 'Done %-% (%).', NEW.trailsection_id, NEW.name, ST_AsText(NEW.shape_2d);
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER hike_trailsection_10_split_geom_iu_tgr
AFTER INSERT OR UPDATE OF shape_2d ON hike_trailsection
FOR EACH ROW EXECUTE PROCEDURE hike_trailsection_event_intersect_split();

-------------------------------------------------------------------------------
-- Change status of related objects when paths are deleted
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION hike_trailsection_related_objects_d() RETURNS trigger AS $$
DECLARE
BEGIN
    -- Mark empty topologies as deleted
    UPDATE hike_event e
        SET deleted = TRUE
        FROM hike_eventtrailsection et
        WHERE et.evnt = e.event_id AND et.trailsection = OLD.trailsection_id AND NOT EXISTS(
            SELECT * FROM hike_eventtrailsection
            WHERE evnt = e.event_id AND trailsection != OLD.trailsection_id
        );

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS hike_trailsection_related_objects_d_tgr ON hike_trailsection;
CREATE TRIGGER hike_trailsection_related_objects_d_tgr
BEFORE DELETE ON hike_trailsection
FOR EACH ROW EXECUTE PROCEDURE hike_trailsection_related_objects_d();

-------------------------------------------------------------------------------
-- Auto force shape_2d into a 3D shape with 0 z-index: new ts insert
-------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION hikster_trailsection_shape_force3d() RETURNS trigger AS $$
BEGIN
    UPDATE hike_trailsection
        SET shape=ST_Force3D(shape_2d)
        WHERE trailsection_id=NEW.trailsection_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER hikster_new_trailsection_shape_force3dtrg
AFTER INSERT OR UPDATE OF shape_2d ON hike_trailsection
FOR EACH ROW EXECUTE PROCEDURE hikster_trailsection_shape_force3d();
