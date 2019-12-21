--------------------------------------------------------------------------
-- This is essentially the same with 40_hike_trailsection_triggers
-- except this has no difficulty column since it is already removed
--------------------------------------------------------------------------
-------------------------------------------------------------------------------
-- Split paths when crossing each other
-------------------------------------------------------------------------------

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
                        INSERT INTO hike_trailsection (objectid,
                                                 visible,
                                                 "valid",
                                                 "name",
                                                 "comments",
                                                 departure,
                                                 arrival,
                                                 external_id,
                                                 shape_2d)
                            VALUES (NEW.objectid,
                                    NEW.visible,
                                    NEW.valid,
                                    NEW.name,
                                    NEW.comments,
                                    NEW.departure,
                                    NEW.arrival,
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
                        INSERT INTO hike_trailsection (objectid,
                                                 visible,
                                                 "valid",
                                                 "name",
                                                 "comments",
                                                 departure,
                                                 arrival,
                                                 external_id,
                                                 shape_2d)
                            VALUES (troncon.objectid,
                                    troncon.visible,
                                    troncon.valid,
                                    troncon.name,
                                    troncon.comments,
                                    troncon.departure,
                                    troncon.arrival,
                                    troncon.external_id,
                                    segment)
                            RETURNING trailsection_id INTO tid_clone;

                        -- Check if troncon is in the new segment
                        IF ST_Distance(newgeom, segment) = 0 THEN

                            IF troncon.trailsection_activities_uuid IS NOT NULL THEN
                                FOR activity IN SELECT * FROM hike_trailsectionactivities ta WHERE ta.trailsection_uuid = troncon.trailsection_activities_uuid LOOP
                                    RAISE NOTICE 'Inserted activity : % - %', tid_clone, activity.activity_id;
                                    INSERT INTO hike_trailsectionactivity(trail_section_id, activity_id) VALUES(tid_clone, activity.activity_id);
                                END LOOP;
                            ELSE
                                FOR activity in SELECT * FROM hike_trailsectionactivity ta WHERE ta.trail_section_id = troncon.trailsection_id LOOP
                                    RAISE NOTICE 'Inserted activity : % - %', tid_clone, activity.activity_id;
                                    INSERT INTO hike_trailsectionactivity(trail_section_id, activity_id) VALUES(tid_clone, activity.activity_id);
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
