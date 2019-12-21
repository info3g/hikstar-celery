from django.core.management.base import BaseCommand
from django.db import connection, transaction

from hikster.hike.models import EventTrailSection, TrailSection


class Command(BaseCommand):
    help = """Remove all duplicate path (same geom)."""

    def handle(self, *args, **options):
        verbosity = options["verbosity"]
        cursor = connection.cursor()
        query = """
            with relations as (
                SELECT t1.trailsection_id as t1_id, t2.trailsection_id as t2_id
                FROM hike_trailsection t1
                JOIN hike_trailsection t2 ON t1.trailsection_id < t2.trailsection_id
                AND ST_ORDERINGEQUALS(t1.shape_2d, t2.shape_2d)
                ORDER BY t1.trailsection_id, t2.trailsection_id
            )
            SELECT * FROM relations WHERE t1_id NOT IN (SELECT t2_id FROM relations)
        """
        cursor.execute(query)
        list_topologies = cursor.fetchall()

        trailsection_deleted = []

        with transaction.atomic():
            try:
                for t1_pk, t2_pk in list_topologies:
                    t2 = TrailSection.objects.get(pk=t2_pk)
                    EventTrailSection.objects.filter(trailsection_id=t2_pk).update(
                        trailsection_id=t1_pk
                    )
                    trailsection_deleted.append(t2)
                    if verbosity > 1:
                        self.stdout.write(f"Deleting path {t2}")
                    t2.delete()
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"{exc}"))

        if verbosity > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"{len(trailsection_deleted)} duplicate paths have been deleted"
                )
            )
