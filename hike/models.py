import math
import itertools

from decimal import Decimal

from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from hikster.helpers import functions
from hikster.search import types as index_types
from hikster.utils.models import ImageBase
from .managers import TrailManager, TrailSectionManager


class Activity(models.Model):
    name = models.CharField(max_length=250, null=False)
    flat_pace = models.FloatField(verbose_name="flat pace (M)", null=False, default=1)
    ascent_pace = models.FloatField(
        verbose_name="ascent pace (M)", null=False, default=1
    )
    descent_pace = models.FloatField(
        verbose_name="descent pace (M)", null=False, default=1
    )
    dev1 = models.FloatField(verbose_name="dev 1 (M)", null=False, default=1)
    dev2 = models.FloatField(verbose_name="dev 2 (M)", null=False, default=1)
    dev3 = models.FloatField(verbose_name="dev 3 (M)", null=False, default=1)
    dev4 = models.FloatField(verbose_name="dev 4 (M)", null=False, default=1)
    distance1 = models.FloatField(verbose_name="distance 1 (KM)", null=False, default=1)
    distance2 = models.FloatField(verbose_name="distance 2 (KM)", null=False, default=1)
    distance3 = models.FloatField(verbose_name="distance 3 (KM)", null=False, default=1)
    distance4 = models.FloatField(verbose_name="distance 4 (KM)", null=False, default=1)

    class Meta:
        verbose_name = "Activity"
        verbose_name_plural = "Activities"

    def __str__(self):
        return "Activity {0}: {1}".format(self.pk, self.name)


class TrailActivity(models.Model):
    DIFFICULTY_BEGINNER = 1
    DIFFICULTY_MODERATE = 2
    DIFFICULTY_INTERMEDIATE = 3
    DIFFICULTY_ADVANCED = 4
    DIFFICULTY_EXPERT = 5
    DIFFICULTY_CHOICES = (
        (DIFFICULTY_BEGINNER, "Débutant"),
        (DIFFICULTY_MODERATE, "Modéré"),
        (DIFFICULTY_INTERMEDIATE, "Intermédiaire"),
        (DIFFICULTY_ADVANCED, "Soutenu"),
        (DIFFICULTY_EXPERT, "Exigeant"),
    )

    trail = models.ForeignKey(
        "Trail", on_delete=models.CASCADE, related_name="activities"
    )
    activity = models.ForeignKey(
        "Activity", on_delete=models.CASCADE, related_name="trails"
    )
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES, null=True, blank=True)
    duration = models.IntegerField(
        null=True, blank=True, help_text="Duration, in minutes"
    )

    class Meta:
        verbose_name_plural = "trail activities"

    def calculate_duration(self):
        length = self.trail.total_length
        ascent = self.trail.height_positive
        descent = self.trail.height_negative

        if length is None or ascent is None or descent is None:
            self.duration = None
            return

        ascent_duration = ascent / self.activity.ascent_pace

        descent_duration = 0
        if self.activity.descent_pace != 0:
            descent_duration = -descent / self.activity.descent_pace

        flat_duration = length / self.activity.flat_pace

        duration_hours = ascent_duration + descent_duration + flat_duration
        duration_minutes = int(duration_hours * 60)

        #
        # Round up to the nearest 15 minutes
        #
        duration_rounded = (int(duration_minutes / 15) + 1) * 15

        self.duration = duration_rounded

    def calculate_difficulty(self):
        length = self.trail.total_length
        ascent = self.trail.height_positive
        descent = self.trail.height_negative

        if length is None or ascent is None or descent is None:
            self.difficulty = None
            return

        ascent_descent = ascent
        if self.activity.descent_pace != 0:
            ascent_descent -= descent

        for x in [1, 2, 3, 4]:
            distance = getattr(self.activity, "distance{}".format(x))
            dev = getattr(self.activity, "dev{}".format(x))

            if self._test_difficulty(length, distance, ascent_descent, dev):
                self.difficulty = self.DIFFICULTY_CHOICES[x - 1][0]
                return

        self.difficulty = self.DIFFICULTY_CHOICES[4][0]

    @staticmethod
    def _test_difficulty(length, distance, ascent_descent, dev):
        length_km = length / 1000
        return ((length_km / distance) ** 2 + (ascent_descent / dev) ** 2) < 1


class TrailSection(models.Model):
    objectid = models.IntegerField(null=True, blank=True)
    trailsection_id = models.AutoField(primary_key=True)
    shape = models.GeometryField(null=True, blank=True, srid=4326, dim=3)
    hikster_creation = models.IntegerField(null=True, blank=True)
    # 2017/07/11 Matty: in_trail field was used to decide which trail section should be shown on Map
    # in_trail = models.IntegerField(default=0)

    """
    2017/07/11 Matty Wang
    Changes made to Trail Section Model due to Hikster decision of implementing DB level triggers as Geotrek
    to automatically split/merge paths
    Geotrek is an open source project: https://github.com/GeotrekCE/Geotrek-admin

    older entries that existed before adding date_insert and date_update were given default value of the date
    when the new model is implemented
    """

    date_insert = models.DateTimeField(auto_now_add=True, editable=False)
    date_update = models.DateTimeField(auto_now=True, editable=False)
    departure = models.CharField(null=True, blank=True, default="", max_length=250)
    arrival = models.CharField(null=True, blank=True, default="", max_length=250)
    valid = models.BooleanField(default=True)
    visible = models.BooleanField(default=True)
    name = models.CharField(null=True, blank=True, max_length=20)
    comments = models.TextField(null=True, blank=True)
    # external_id was introduced here because it appeared in Geotrek's triggers; not sure yet how relevant it is for us
    external_id = models.CharField(max_length=128, blank=True, null=True)
    shape_2d = models.LineStringField(
        blank=True, null=True, srid=4326, dim=2, spatial_index=False
    )
    ascent = models.IntegerField(
        default=0, null=True, blank=True
    )  # denivellee_positive
    descent = models.IntegerField(
        default=0, null=True, blank=True
    )  # denivellee_negative
    min_elevation = models.IntegerField(
        default=0, null=True, blank=True
    )  # altitude_minimum
    max_elevation = models.IntegerField(
        default=0, null=True, blank=True
    )  # altitude_maximum
    slope = models.FloatField(null=True, blank=True, default=0.0)  # pente
    lgth = models.FloatField(default=0.0, null=True, blank=True)
    trailsection_activities_uuid = models.CharField(
        max_length=60, null=True, blank=True
    )

    objects_with_eager_loading = TrailSectionManager()
    objects = models.Manager()

    def __str__(self):
        return f"{self.trailsection_id} - {self.name}"

    @property
    def activity_ids(self):
        return self.activities.values_list("activity__id", flat=True)


class TrailsectionActivities(models.Model):
    trailsection_uuid = models.CharField(max_length=60, null=True, blank=True)
    activity_id = models.IntegerField()


class EventTrailSection(models.Model):
    eventtrailsection_id = models.AutoField(primary_key=True)
    trailsection = models.ForeignKey(
        TrailSection, db_column="trailsection", null=False, on_delete=models.CASCADE
    )
    evnt = models.ForeignKey(
        "Event", db_column="evnt", null=False, on_delete=models.CASCADE
    )
    start_position = models.FloatField(db_index=True)
    end_position = models.FloatField(db_index=True)
    order = models.IntegerField(default=0, blank=True, null=True)

    def __str__(self):
        return f"Event Trail Section: {self.eventtrailsection_id} on {self.trailsection} of {self.evnt}"

    def save(self, *args, **kwargs):
        # when eventtrailsection is saved; event will be able to have a computed shape in 2d
        return super(EventTrailSection, self).save(*args, **kwargs)


class Event(models.Model):
    event_id = models.OneToOneField(
        "Trail",
        db_column="event_id",
        to_field="trail_id",
        primary_key=True,
        on_delete=models.CASCADE,
    )
    date_insert = models.DateTimeField(auto_now_add=True, editable=False)
    date_update = models.DateTimeField(auto_now=True, editable=False)
    deleted = models.BooleanField(editable=False, default=False)
    shape = models.GeometryField(
        dim=3, srid=4326, null=True, blank=True, default=None
    )  # geom_3d
    lgth = models.FloatField(default=0.0, null=True, blank=True)
    ascent = models.IntegerField(
        default=0, null=True, blank=True
    )  # denivellee_positive
    descent = models.IntegerField(
        default=0, null=True, blank=True
    )  # denivellee_negative
    min_elevation = models.IntegerField(
        default=0, null=True, blank=True
    )  # altitude_minimum
    max_elevation = models.IntegerField(
        default=0, null=True, blank=True
    )  # altitude_maximum
    slope = models.FloatField(null=True, blank=True, default=0.0)  # pente
    e_offset = models.FloatField(default=0.0)  # in SRID units; decallage
    kind = models.CharField(max_length=32, blank=True, null=True)
    shape_2d = models.GeometryField(
        srid=4326, null=True, default=None, spatial_index=False
    )  # geom

    trailsections = models.ManyToManyField(TrailSection, through="EventTrailSection")

    exist_before = models.BooleanField(editable=False, default=False)

    def __str__(self):
        return f"{self.event_id} Event"

    def save(self, *args, **kwargs):
        return super(Event, self).save(*args, **kwargs)


class Trail(models.Model):
    PATH_TYPES = (
        (0, "Non determine"),
        (1, "Aller simple"),
        (2, "Boucle"),
        (3, "Aller-retour"),
    )

    id_field = "trail_id"
    index_type = index_types.TYPE_TRAIL

    objectid = models.IntegerField(null=True, blank=True)
    trail_id = models.AutoField(primary_key=True)
    slug = models.SlugField(max_length=300, default="", blank=True)
    trail_type = models.IntegerField(default=1)
    name = models.CharField(max_length=250, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    total_length = models.FloatField(null=True, blank=True)
    min_elevation = models.IntegerField(
        default=0, null=True, blank=True
    )  # altitude_minimum
    max_elevation = models.IntegerField(
        default=0, null=True, blank=True
    )  # altitude_maximum
    path_type = models.IntegerField(choices=PATH_TYPES, null=True, blank=True)
    height_positive = models.IntegerField(null=True, blank=True)
    height_negative = models.IntegerField(null=True, blank=True)
    height_difference = models.IntegerField(null=True, blank=True)
    private = models.BooleanField(default=False)
    hikster_creation = models.IntegerField(null=True, blank=True)
    shape = models.GeometryField(srid=4326, null=True, blank=True, dim=3)
    opening_dates = JSONField(null=True, blank=True)
    last_modified = models.DateField(auto_now=True)

    # Related fields
    location = models.ForeignKey(
        "location.Location",
        related_name="trails",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    region = models.ForeignKey(
        "location.Location", null=True, blank=True, on_delete=models.SET_NULL
    )
    trail_sections = models.ManyToManyField(TrailSection, blank=True)

    # Managers
    objects = models.Manager()
    objects_with_eager_loading = TrailManager()

    shape_2d = models.GeometryField(srid=4326, null=True, blank=True, dim=2)

    @property
    def object_type(self):
        return self.__class__.__name__

    def format_duration(self, duration):
        return functions.pretty_time_delta(duration.total_seconds())

    def __str__(self):
        value = f"{self.trail_id} Trail name: {self.name}"

        if self.location:
            value = f"{value} - Park: {self.location.pk}"

        return value

    def save(self, *args, **kwargs):
        self.slug = original = slugify(self.name)

        for x in itertools.count(1):
            if not Trail.objects.filter(slug=self.slug).exists():
                break
            self.slug = "%s-%d" % (original, x)

        super(Trail, self).save(*args, **kwargs)
        trailAcivities = TrailActivity.objects.filter(trail_id=self.trail_id)
        for trailActivity in trailAcivities:
            trailActivity.calculate_difficulty
            trailActivity.calculate_duration
            trailActivity.save()

    @property
    def activity_names(self):
        return self.activities.values_list("activity__name", flat=True)

    @property
    def banner(self):
        return self.images.banners().first()

    @property
    def activity_ids(self):
        return self.activities.values_list("activity__id", flat=True)

    @property
    def markers(self):
        event_trail_sections = list(
            EventTrailSection.objects.filter(evnt=self.event)
            .values("start_position", "end_position", "trailsection")
            .order_by("order")
        )
        return event_trail_sections

    @cached_property
    def difficulty(self):
        activity = self.activities.order_by("difficulty").first()
        return activity.get_difficulty_display() if activity else ""

    @cached_property
    def duration(self):
        activity = self.activities.order_by("duration").first()
        if activity is None:
            return "-"
        duration = activity.duration
        hours = math.floor(duration / 60)
        minutes = duration % 60
        return f"{hours}h{minutes}"


class TrailSectionActivity(models.Model):
    trail_section = models.ForeignKey(
        TrailSection, on_delete=models.CASCADE, related_name="activities"
    )
    activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name="trail_sections"
    )

    class Meta:
        verbose_name = _("Trail Section Activity")
        verbose_name = _("Trail Section Activities")
        unique_together = ("trail_section", "activity")

    def __str__(self):
        return f"Trail section: {self.trail_section.trailsection_id} - {self.activity.name}"


class TrailImage(ImageBase):
    parent_field = "trail"

    trail = models.ForeignKey(Trail, on_delete=models.CASCADE, related_name="images")


class TrailStep(models.Model):
    trail = models.ForeignKey("Trail", on_delete=models.CASCADE, related_name="steps")
    lat = models.DecimalField(max_digits=19, decimal_places=16, default=Decimal("0"))
    lng = models.DecimalField(max_digits=19, decimal_places=16, default=Decimal("0"))
    point = models.PointField()
    order = models.SmallIntegerField()

    class Meta:
        verbose_name = _("Trail Step")
        verbose_name_plural = _("Trail Steps")
