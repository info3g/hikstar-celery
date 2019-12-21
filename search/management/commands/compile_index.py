from django.core.management.base import BaseCommand
from hikster.hike.models import Trail
from hikster.location.models import Location
from hikster.search.models import Index


class Command(BaseCommand):
    help = 'Re-builds the index table'

    def handle(self, *args, **options):
        self.stdout.write('Adding locations...')
        for location in Location.objects.all():
            Index.objects.add(location)

        self.stdout.write('Adding trails...')
        for trail in Trail.objects.all():
            Index.objects.add(trail)
