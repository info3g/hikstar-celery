import itertools
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.utils.text import slugify

from hikster.search import types as index_types
from hikster.utils.models import Address, ImageBase, Contact

from .managers import LocationManager, PointOfInterestManager


POI_CATEGORY = (
    (1, "Hébergement"),
    (2, "Retiré (poste d'accueil)"),
    (3, "Stationnement"),
    (4, "Activité"),
    (5, "Restaurant"),
    (6, "Autre"),
)

LOCATION_MUNICIPALITY = 8
LOCATION_MOUNTAIN = 9
LOCATION_REGION = 10
LOCATION_NETWORK = 11
LOCATION_TYPE = (
    (LOCATION_MUNICIPALITY, "Municipalité"),
    (LOCATION_MOUNTAIN, "Mont"),
    (LOCATION_REGION, "Région touristique"),
    (LOCATION_NETWORK, "Réseau"),
)


class LocationQuerySet(models.QuerySet):
    def regions(self, **kwargs):
        return self.filter(type=LOCATION_REGION, **kwargs)


# Create your models here.
class Location(models.Model):
    id_field = "location_id"

    organization = models.ForeignKey(
        "organizations.Organization",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="locations",
    )
    objectid = models.IntegerField(null=True, blank=True)
    location_id = models.AutoField(primary_key=True)
    slug = models.SlugField(max_length=300, default="", blank=True)
    shape = models.GeometryField(srid=4326, null=True, blank=True)
    name = models.CharField(max_length=250, null=True)
    type = models.IntegerField(choices=LOCATION_TYPE, null=True, blank=True)
    parking = models.IntegerField(null=True, blank=True)
    network = models.CharField(max_length=100, null=True, blank=True)
    dog_allowed = models.BooleanField()
    living_rules = models.TextField(blank=True, null=True)
    fare_note = models.TextField(null=True, blank=True)
    transport = models.TextField(null=True, blank=True)
    schedule = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    network_length = models.FloatField(null=True, blank=True)
    exploitation_periods = JSONField(null=True, blank=True)
    last_modified = models.DateField(auto_now=True)
    modified_date = models.DateTimeField(auto_now=True)
    deletion_pending = models.BooleanField(default=False)

    # Relations
    contact = models.ManyToManyField(Contact, blank=True)
    address = models.ForeignKey(
        Address, blank=True, null=True, on_delete=models.SET_NULL
    )

    # Custom managers
    objects_with_eager_loading = LocationManager()
    objects = LocationQuerySet.as_manager()

    @property
    def object_type(self):
        return self.__class__.__name__

    def __str__(self):
        return "{} ({})".format(self.name, self.get_type_display())

    @property
    def index_type(self):
        type_map = {
            LOCATION_REGION: index_types.TYPE_REGION,
            LOCATION_NETWORK: index_types.TYPE_NETWORK,
            LOCATION_MOUNTAIN: index_types.TYPE_MOUNTAIN,
            LOCATION_MUNICIPALITY: index_types.TYPE_MUNICIPALITY,
        }
        try:
            return type_map[self.type]

        except KeyError:
            return index_types.TYPE_LOCATION

    def save(self, *args, **kwargs):
        self.slug = original = slugify(self.name)
        self.objectid = self.location_id

        for x in itertools.count(1):
            if not Location.objects.filter(slug=self.slug).exists():
                break
            self.slug = "%s-%d" % (original, x)

        super(Location, self).save(*args, **kwargs)


class LocationImage(ImageBase):
    parent_field = "location"

    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="images"
    )


class PointOfInterestType(models.Model):
    category = models.IntegerField(choices=POI_CATEGORY, null=True, blank=True)
    name = models.CharField(max_length=250)

    def __str__(self):
        return f"{self.id} - {self.name}"


class PointOfInterest(models.Model):
    id_field = "poi_id"

    organization = models.ForeignKey(
        "organizations.Organization", null=True, blank=True, on_delete=models.SET_NULL
    )
    objectid = models.IntegerField(null=True, blank=True)
    poi_id = models.AutoField(primary_key=True)
    slug = models.SlugField(max_length=300, default="", blank=True)
    shape = models.GeometryField(srid=4326, null=True, blank=True)
    name = models.CharField(max_length=250, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    premium = models.BooleanField(default=False)
    fare = models.TextField(null=True, blank=True)
    owner = models.CharField(max_length=250, null=True, blank=True)
    position_quality = models.IntegerField(default=0)
    visible_in_map = models.IntegerField(default=0)

    type = models.ForeignKey(
        PointOfInterestType,
        related_name="Polygon_of_interests",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    category = models.IntegerField(choices=POI_CATEGORY, null=True, blank=True)
    address = models.ForeignKey(
        Address, blank=True, null=True, on_delete=models.SET_NULL
    )
    contact = models.ManyToManyField(Contact, blank=True)
    location = models.ManyToManyField(Location, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    objects_with_eager_loading = PointOfInterestManager()
    objects = models.Manager()

    def __str__(self):
        name = f"{self.poi_id} : {self.name}"
        if self.type:
            name = f"{name} - {self.type.name}"
        return name

    def save(self, *args, **kwargs):
        self.slug = original = slugify(self.name)
        self.objectid = self.poi_id

        for x in itertools.count(1):
            if not PointOfInterest.objects.filter(slug=self.slug).exists():
                break
            self.slug = "%s-%d" % (original, x)

        super(PointOfInterest, self).save(*args, **kwargs)
        if not self.objectid:
            self.objectid = self.poi_id
            self.save()

    @property
    def object_type(self):
        return self.__class__.__name__

    @property
    def title(self):
        return self.name or self.type.get_category_display()


class PointOfInterestImage(ImageBase):
    parent_field = "location"

    location = models.ForeignKey(
        PointOfInterest, on_delete=models.CASCADE, related_name="images"
    )
