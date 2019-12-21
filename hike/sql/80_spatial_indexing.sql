DROP INDEX IF EXISTS event_shape2d_idx;

CREATE INDEX event_shape2d_idx ON hike_event USING gist(shape_2d);

DROP INDEX IF EXISTS trailsection_shape2d_idx;

CREATE INDEX trailsection_shape2d_idx ON hike_trailsection USING gist(shape_2d);

DROP INDEX IF EXISTS trailsection_start_point_idx;

CREATE INDEX trailsection_start_point_idx ON hike_trailsection USING gist(ST_StartPoint(shape_2d));

DROP INDEX IF EXISTS trailsection_end_point_idx;

CREATE INDEX trailsection_end_point_idx ON hike_trailsection USING gist(ST_EndPoint(shape_2d));

DROP INDEX IF EXISTS trailsection_shape_idx;

CREATE INDEX trailsection_shape_idx ON hike_trailsection USING gist(shape);