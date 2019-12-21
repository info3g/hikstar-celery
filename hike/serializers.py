from collections import OrderedDict

from expander import ExpanderSerializerMixin
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from hikster.helpers import mixins, functions
from .models import (
    Trail,
    TrailImage,
    Activity,
    TrailActivity,
    TrailSection,
    Event,
    EventTrailSection,
)
from hikster.location.serializers import LocationSerializer
from hikster.utils.serializers import ImageSerializerBase


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ("id", "name")


class TrailActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = TrailActivity
        fields = ["activity", "difficulty", "duration"]


class TrailSectionSerializer(
    ExpanderSerializerMixin,
    mixins.IncludeFieldsMixin,
    mixins.ExcludeFieldsMixin,
    serializers.ModelSerializer,
):
    class Meta:
        model = TrailSection
        exclude = ("objectid",)


class IntegerListField(serializers.ListField):
    child = serializers.CharField()


class TrailImageSerializer(ImageSerializerBase):
    class Meta:
        model = TrailImage
        exclude = ["id", "trail"]


class TrailSerializer(
    ExpanderSerializerMixin,
    mixins.IncludeFieldsMixin,
    mixins.ExcludeFieldsMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(source="trail_id", required=False, read_only=True)
    object_type = serializers.ReadOnlyField()
    url = serializers.HyperlinkedIdentityField(view_name="trail-detail", read_only=True)
    location_name = serializers.CharField(read_only=True, source="location.name")
    activities = TrailActivitySerializer(many=True)
    banner = serializers.SerializerMethodField(read_only=True)
    difficulty = serializers.CharField(read_only=True)
    duration = serializers.CharField(read_only=True)

    class Meta:
        model = Trail
        exclude = ["trail_sections"]
        expandable_fields = {
            "images": (TrailImageSerializer, (), {"many": True}),
            "location": LocationSerializer,
        }

    def get_banner(self, obj):
        if obj.banner and obj.banner.image:
            return self.context["request"].build_absolute_uri(obj.banner.image.url)
        return ""

    def validate(self, attrs):
        if not attrs["name"] or not attrs["description"]:
            raise serializers.ValidationError(
                "Veuillez entrer un nom ou une description pour votre sentier."
            )
        return attrs

    def create(self, validated_data):
        images = validated_data.pop("images", None)
        region = validated_data.pop("region", None)
        location = validated_data.pop("location", None)
        activities = validated_data.pop("activities", None)

        # We save the new location as usual
        TrailClass = self.Meta.model
        trail = TrailClass(**validated_data)

        if location and location is not None:
            trail.location = location

        if region and region is not None:
            trail.region = region

        trail.save()

        if images:
            trail.images = functions.save_nested(images, TrailImageSerializer)

        if activities:
            for activity in activities:
                try:
                    TrailActivity.objects.get(trail=trail, activity=activity)
                except TrailActivity.DoesNotExist:
                    TrailActivity.objects.create(trail=trail, activity=activity)

        user = self.context["request"].user
        trail.owner.add(user.trailadmin)

        return trail

    def update(self, trail: Trail, validated_data: OrderedDict):
        images = validated_data.pop("images", None)
        location = validated_data.pop("location", None)
        region = validated_data.pop("region", None)
        activities = validated_data.pop("activities", None)

        trail_id = trail.trail_id

        for key, value in validated_data.items():
            setattr(trail, key, value)

        # check whether the trail already exists in Event model as an event or not
        # if it does, delete it and trigger will create a new one
        if Event.objects.filter(event_id=trail_id).exists():
            EventTrailSection.objects.filter(evnt=trail.trail_id).delete()

        # Save foreign key related fields
        # Different from normal nested relations: we just have to link it to a currently existing model
        if location and location is not None:
            trail.location = location

        if region and region is not None and region.type == 10:
            trail.region = region

        trail.save()

        if activities:
            trail.activities.delete()
            for activity in activities:
                try:
                    TrailActivity.objects.get(trail=trail, activity=activity)
                except TrailActivity.DoesNotExist:
                    TrailActivity.objects.create(trail=trail, activity=activity)

        # Save nested representations
        if images:
            if not trail.images.all().exists():
                trail.images = functions.save_nested(images, TrailImageSerializer)
            else:
                existing_img = set(trail.images.values_list("id", flat=True))
                img_to_update = set([image["id"] for image in images if "id" in image])

                # If the ids are in the the remainder of the diff between the existing img and the img to update
                # it means we've deleted it in the ui
                trail.images.filter(id__in=existing_img - img_to_update).delete()

                # We save the new images as usual, which equals to adding it to the existing ones after clearing the
                for image in images:
                    img = TrailImage(**image)
                    img.save()
                    trail.images.add(img)
        else:
            trail.images.all().delete()

        return trail


class Trail3DSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Trail
        geo_field = "shape"
        fields = ("trail_id", "shape")


#################################################################
#              Add Event and Event TrailSection                 #
#################################################################


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = "__all__"


class EventTrailSectionSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        many = kwargs.pop("many", True)
        super(EventTrailSectionSerializer, self).__init__(many=many, *args, **kwargs)

    class Meta:
        model = EventTrailSection
        fields = "__all__"
