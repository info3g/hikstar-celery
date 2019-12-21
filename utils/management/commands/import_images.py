import json
import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand

from hikster.hike.models import Trail, TrailImage
from hikster.location.models import Location, LocationImage, \
    PointOfInterest, PointOfInterestImage
from hikster.utils.models import get_image_upload_to


BASE_IMAGE_DIR = '/home/freebsd/images'


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('import_file', nargs=1, type=str)

    def handle(self, *args, **options):
        filename = options['import_file'][0]
        with open(filename) as fp:
            data = json.load(fp)
        self.get_trail_images(data['trails'])
        self.get_location_images(data['locations'])
        self.get_poi_images(data['pois'])

    def get_trail_images(self, data):
        for trail_id, images in data.items():
            try:
                t = Trail.objects.get(trail_id=trail_id)
            except Trail.DoesNotExist:
                print('TRAIL NOT FOUND: {}'.format(trail_id))
                continue
            for image in images:
                print('IMAGE: {}'.format(image))
                img_path = os.path.join(BASE_IMAGE_DIR, image['image'])
                try:
                    ti = TrailImage.objects.get(
                        trail=t,
                        old_image=image['image']
                    )
                    print('    FOUND')
                except TrailImage.DoesNotExist:
                    ti = TrailImage(
                        trail=t,
                        image_type=image['type'],
                        old_image=image['image']
                    )
                    print('    CREATED')
                new_img_name = ti.image.name
                if not new_img_name:
                    new_img_name = get_image_upload_to(ti, img_path)
                    print('    NEW NAME: {}'.format(new_img_name))
                else:
                    print('    NAME: {}'.format(new_img_name))
                new_img_path = os.path.join(settings.MEDIA_ROOT, new_img_name)
                if not os.path.exists(os.path.dirname(new_img_path)):
                    os.mkdir(os.path.dirname(new_img_path))
                shutil.copyfile(img_path, new_img_path)
                ti.image.name = new_img_name
                ti.save()

    def get_location_images(self, data):
        for location_id, images in data.items():
            try:
                l = Location.objects.get(location_id=location_id)
            except Location.DoesNotExist:
                print('LOCATION NOT FOUND: {}'.format(location_id))
                continue
            for image in images:
                print('IMAGE: {}'.format(image))
                img_path = os.path.join(BASE_IMAGE_DIR, image['image'])
                try:
                    li = LocationImage.objects.get(
                        location=l,
                        old_image=image['image']
                    )
                    print('    FOUND')
                except LocationImage.DoesNotExist:
                    li = LocationImage(
                        location=l,
                        image_type=image['type'],
                        old_image=image['image']
                    )
                    print('    CREATED')
                new_img_name = li.image.name
                if not new_img_name:
                    new_img_name = get_image_upload_to(li, img_path)
                    print('    NEW NAME: {}'.format(new_img_name))
                else:
                    print('    NAME: {}'.format(new_img_name))
                new_img_path = os.path.join(settings.MEDIA_ROOT, new_img_name)
                if not os.path.exists(os.path.dirname(new_img_path)):
                    os.mkdir(os.path.dirname(new_img_path))
                shutil.copyfile(img_path, new_img_path)
                li.image.name = new_img_name
                li.save()

    def get_poi_images(self, data):
        for poi_id, images in data.items():
            try:
                p = PointOfInterest.objects.get(poi_id=poi_id)
            except PointOfInterest.DoesNotExist:
                print('POI NOT FOUND: {}'.format(poi_id))
                continue
            for image in images:
                print('IMAGE: {}'.format(image))
                img_path = os.path.join(BASE_IMAGE_DIR, image['image'])
                try:
                    pi = PointOfInterestImage.objects.get(
                        location=p,
                        old_image=image['image']
                    )
                    print('    FOUND')
                except PointOfInterestImage.DoesNotExist:
                    pi = PointOfInterestImage(
                        location=p,
                        image_type=image['type'],
                        old_image=image['image']
                    )
                    print('    CREATED')
                new_img_name = pi.image.name
                if not new_img_name:
                    new_img_name = get_image_upload_to(pi, img_path)
                    print('    NEW NAME: {}'.format(new_img_name))
                else:
                    print('    NAME: {}'.format(new_img_name))
                new_img_path = os.path.join(settings.MEDIA_ROOT, new_img_name)
                if not os.path.exists(os.path.dirname(new_img_path)):
                    os.mkdir(os.path.dirname(new_img_path))
                shutil.copyfile(img_path, new_img_path)
                pi.image.name = new_img_name
                pi.save()
