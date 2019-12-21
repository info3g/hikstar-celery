-------------------------------------------------------------------------------
-- Alter ForeignKey to trailsection in order to add CASCADE behavior at DB-level - TODO: double check
-------------------------------------------------------------------------------


-------------------------------------------------------------------------------
-- Compute geometry of events
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION hike_eventtrailsection_geometry() RETURNS trigger AS $$
DECLARE
    eid integer;
    eids integer[];
BEGIN
    IF TG_OP = 'INSERT' THEN
        eids := array_append(eids, NEW.evnt);
    ELSE
        eids := array_append(eids, OLD.evnt);
        IF TG_OP = 'UPDATE' THEN -- /!\ Logical ops are commutative in SQL
            IF NEW.evnt != OLD.evnt THEN
                eids := array_append(eids, NEW.evnt);
            END IF;
        END IF;
    END IF;

    FOREACH eid IN ARRAY eids LOOP
        PERFORM update_geometry_of_evenement(eid);
    END LOOP;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS hike_eventtrailsection_geometry_tgr ON hike_eventtrailsection;
CREATE TRIGGER hike_eventtrailsection_geometry_tgr
AFTER INSERT OR UPDATE ON hike_eventtrailsection
FOR EACH ROW EXECUTE PROCEDURE hike_eventtrailsection_geometry();

-------------------------------------------------------------------------------
-- Emulate junction points
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION hike_eventtrailsection_junction_point_iu() RETURNS trigger AS $$
DECLARE
    junction geometry;
    t_count integer;
BEGIN
    -- Deal with previously connected paths in the case of an UDPATE action
    IF TG_OP = 'UPDATE' THEN
        -- There were connected paths only if it was a junction point
        IF OLD.start_position = OLD.end_position AND OLD.start_position IN (0.0, 1.0) THEN
            DELETE FROM hike_eventtrailsection
            WHERE eventtrailsection_id != OLD.eventtrailsection_id AND evnt = OLD.evnt;
        END IF;
    END IF;

    -- Don't proceed for non-junction points
    IF NEW.start_position != NEW.end_position OR NEW.start_position NOT IN (0.0, 1.0) THEN
        RETURN NULL;
    END IF;

    -- Don't proceed for intermediate markers (forced passage) : if this
    -- is not the only evenement_troncon, then it's an intermediate marker.
    SELECT count(*)
        INTO t_count
        FROM hike_eventtrailsection et
        WHERE et.evnt = NEW.evnt;
    IF t_count > 1 THEN
        RETURN NULL;
    END IF;

    -- Deal with newly connected paths
    IF NEW.start_position = 0.0 THEN
        SELECT ST_StartPoint(shape_2d) INTO junction FROM hike_trailsection WHERE trailsection_id = NEW.trailsection;
    ELSIF NEW.start_position = 1.0 THEN
        SELECT ST_EndPoint(shape_2d) INTO junction FROM hike_trailsection WHERE trailsection_id = NEW.trailsection;
    END IF;

    INSERT INTO hike_eventtrailsection (trailsection, evnt, start_position, end_position)
    SELECT trailsection_id, NEW.evnt, 0.0, 0.0 -- Troncon departing from this junction
    FROM hike_trailsection t
    WHERE trailsection_id != NEW.trailsection AND ST_StartPoint(shape_2d) = junction AND NOT EXISTS (
        -- prevent trigger recursion
        SELECT * FROM hike_eventtrailsection WHERE trailsection = t.trailsection_id AND evnt = NEW.evnt
    )
    UNION
    SELECT trailsection_id, NEW.evnt, 1.0, 1.0-- Troncon arriving at this junction
    FROM hike_trailsection t
    WHERE trailsection_id != NEW.trailsection AND ST_EndPoint(shape_2d) = junction AND NOT EXISTS (
        -- prevent trigger recursion
        SELECT * FROM hike_eventtrailsection WHERE trailsection = t.trailsection_id AND evnt = NEW.evnt
    );

    RETURN NULL;
END;
$$ LANGUAGE plpgsql VOLATILE;
-- VOLATILE is the default but I prefer to set it explicitly because it is
-- required for this case (in order to avoid trigger cascading)

DROP TRIGGER IF EXISTS hike_eventtrailsection_junction_point_iu_tgr ON hike_eventtrailsection;
CREATE TRIGGER hike_eventtrailsection_junction_point_iu_tgr
AFTER INSERT OR UPDATE OF start_position, end_position ON hike_eventtrailsection
FOR EACH ROW EXECUTE PROCEDURE hike_eventtrailsection_junction_point_iu();
