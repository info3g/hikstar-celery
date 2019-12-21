-------------------------------------------------------------------------------
-- INSERT into hike_trail triggers INSERT into hike_event
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION creating_new_trail_creates_event() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO hike_event(deleted, e_offset, kind, event_id, exist_before)
	VALUES (False, 0, '', NEW.trail_id, False);

	RETURN NEW;

END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS creating_new_trail_creates_event_tgr ON hike_trail;
CREATE TRIGGER creating_new_trail_creates_event_tgr
BEFORE INSERT ON hike_trail
FOR EACH ROW EXECUTE PROCEDURE creating_new_trail_creates_event();
