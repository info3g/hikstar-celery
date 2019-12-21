CREATE OR REPLACE FUNCTION ft_merge_path(updated integer, merged integer)
  RETURNS boolean AS $$

DECLARE
    element RECORD;
    rebuild_line geometry;
    updated_geom geometry;
    merged_geom geometry;
    reverse_update boolean;
    reverse_merged boolean;
    max_snap_distance float;

BEGIN
    reverse_update := FALSE;
    reverse_merged := FALSE;
    -- 2 is PATH_MERGE_SNAPPING_DISTANCE; used in Geotrek's setting to indicate the minimum length to merge the trailsection
    max_snap_distance := 0.00004;
    rebuild_line := NULL;

    IF updated = merged
    THEN
        -- can't merged a path itself !
        return FALSE;

    END IF;

    updated_geom := (SELECT shape_2d FROM hike_trailsection WHERE trailsection_id = updated);
    merged_geom := (SELECT shape_2d FROM hike_trailsection WHERE trailsection_id = merged);

    -- DETECT matching point to rebuild path line
    IF ST_EQUALS(ST_STARTPOINT(updated_geom), ST_STARTPOINT(merged_geom))
    THEN
	rebuild_line := ST_MAKELINE(ST_REVERSE(updated_geom), merged_geom);
	reverse_update := TRUE;

    ELSIF ST_EQUALS(ST_STARTPOINT(updated_geom), ST_ENDPOINT(merged_geom))
    THEN
	rebuild_line := ST_MAKELINE(ST_REVERSE(updated_geom), ST_REVERSE(merged_geom));
	reverse_update := TRUE;
	reverse_merged := TRUE;

    ELSIF ST_EQUALS(ST_ENDPOINT(updated_geom), ST_ENDPOINT(merged_geom))
    THEN
	rebuild_line := ST_MAKELINE(updated_geom, ST_REVERSE(merged_geom));
	reverse_merged := TRUE;

    ELSIF ST_EQUALS(ST_ENDPOINT(updated_geom), ST_STARTPOINT(merged_geom))
    THEN
	rebuild_line := ST_MAKELINE(updated_geom, merged_geom);

    ELSIF (ST_DISTANCE(ST_STARTPOINT(updated_geom), ST_STARTPOINT(merged_geom))::float <= max_snap_distance)
    THEN
	rebuild_line := ST_MAKELINE(ST_REVERSE(updated_geom), merged_geom);
	reverse_update := TRUE;

    ELSIF (ST_DISTANCE(ST_STARTPOINT(updated_geom), ST_ENDPOINT(merged_geom)) <= max_snap_distance)
    THEN
	rebuild_line := ST_MAKELINE(ST_REVERSE(updated_geom), ST_REVERSE(merged_geom));
	reverse_update := TRUE;
	reverse_merged := TRUE;

    ELSIF (ST_DISTANCE(ST_ENDPOINT(updated_geom), ST_ENDPOINT(merged_geom)) <= max_snap_distance)
    THEN
	rebuild_line := ST_MAKELINE(updated_geom, ST_REVERSE(merged_geom));
	reverse_merged := TRUE;

    ELSIF (ST_DISTANCE(ST_ENDPOINT(updated_geom), ST_STARTPOINT(merged_geom)) <= max_snap_distance)
    THEN
	rebuild_line := ST_MAKELINE(updated_geom, merged_geom);

    ELSE
    -- no snapping -> END !
        RETURN FALSE;

    END IF;

    -- update events on updated path
    FOR element IN
        SELECT * FROM hike_eventtrailsection et
                 JOIN hike_event as evt ON et.evnt=evt.event_id
                 JOIN hike_trailsection as ts on et.trailsection = ts.trailsection_id
        WHERE et.trailsection = updated
    LOOP
        IF reverse_update = TRUE
	THEN
	    -- update reverse pk
	    UPDATE hike_eventtrailsection
		   SET start_position = (1- start_position) * ST_LENGTH(updated_geom) / (ST_LENGTH(updated_geom) + ST_LENGTH(merged_geom)),
		       end_position = (1- end_position) * ST_LENGTH(updated_geom) / (ST_LENGTH(updated_geom) + ST_LENGTH(merged_geom))
		   WHERE eventtrailsection_id = element.eventtrailsection_id;
	    -- update reverse offset
            UPDATE hike_event
                   SET e_offset = -e_offset
                   WHERE event.id = element.evnt;
	ELSE
	    UPDATE hike_eventtrailsection
		   SET start_position = start_position * ST_LENGTH(updated_geom) / (ST_LENGTH(updated_geom) + ST_LENGTH(merged_geom)),
		       end_position = end_position * ST_LENGTH(updated_geom) / (ST_LENGTH(updated_geom) + ST_LENGTH(merged_geom))
		   WHERE eventtrailsection_id = element.eventtrailsection_id;
	END IF;
    END LOOP;

    -- update events on merged path
    FOR element IN
        SELECT * FROM hike_eventtrailsection et
                 JOIN hike_event as evt ON et.evnt=evt.event_id
                 JOIN hike_trailsection as ts on et.trailsection = ts.trailsection_id
        WHERE et.trailsection = merged
    LOOP
        IF reverse_merged = TRUE
        THEN
	    UPDATE hike_eventtrailsection
		   SET start_position = ((1- start_position) * ST_LENGTH(merged_geom) / (ST_LENGTH(updated_geom) + ST_LENGTH(merged_geom))) + (ST_LENGTH(updated_geom) / (ST_LENGTH(updated_geom) + ST_LENGTH(merged_geom))),
		       end_position = ((1- end_position) * ST_LENGTH(merged_geom) / (ST_LENGTH(updated_geom) + ST_LENGTH(merged_geom))) + (ST_LENGTH(updated_geom) / (ST_LENGTH(updated_geom) + ST_LENGTH(merged_geom)))
		   WHERE eventtrailsection_id = element.eventtrailsection_id;

            UPDATE hike_event
                   SET e_offset = -e_offset
                   WHERE event_id = element.event_id;
        ELSE
	    UPDATE hike_eventtrailsection
		   SET start_position = (start_position * ST_LENGTH(merged_geom) / (ST_LENGTH(updated_geom) + ST_LENGTH(merged_geom))) + (ST_LENGTH(updated_geom) / (ST_LENGTH(updated_geom) + ST_LENGTH(merged_geom))),
		       end_position = (end_position * ST_LENGTH(merged_geom) / (ST_LENGTH(updated_geom) + ST_LENGTH(merged_geom))) + (ST_LENGTH(updated_geom) / (ST_LENGTH(updated_geom) + ST_LENGTH(merged_geom)))
		   WHERE eventtrailsection_id = element.eventtrailsection_id;
        END IF;
    END LOOP;

    -- fix new geom to updated
    UPDATE hike_trailsection
           SET shape_2d = rebuild_line
           WHERE trailsection_id = updated;

    -- Link merged events to updated
    UPDATE hike_eventtrailsection
           SET trailsection = updated
           WHERE trailsection = merged;

    -- Delete merged Path
    DELETE FROM hike_trailsection WHERE trailsection_id = merged;

    RETURN TRUE;

END;
$$ LANGUAGE plpgsql;
