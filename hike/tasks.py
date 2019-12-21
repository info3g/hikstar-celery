from django.db import connection

from django_rq import job


@job
def update_geometry_of_evenement(trail_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            DO $$
            BEGIN
                PERFORM update_geometry_of_evenement(%s);
            END;
            $$;
            """,
            [trail_id],
        )
