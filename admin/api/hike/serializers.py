import uuid

from django.contrib.gis.geos import GEOSGeometry, WKTWriter
from django.core.management import call_command
from django.db import connection, transaction
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from hikster.hike.models import (
    EventTrailSection,
    Trail,
    TrailActivity,
    TrailImage,
    TrailSection,
    TrailsectionActivities,
    TrailSectionActivity,
    TrailStep,
)
from hikster.hike.tasks import update_geometry_of_evenement


class TrailSectionActivitySerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="activity.name", read_only=True)

    class Meta:
        model = TrailSectionActivity
        fields = ("id", "activity", "name")


class TrailActivitySerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="activity.name", read_only=True)

    class Meta:
        model = TrailActivity
        fields = ("id", "activity", "name")


class TrailSectionThinSerializer(serializers.ModelSerializer):
    activity_ids = serializers.ListField()

    class Meta:
        model = TrailSection
        fields = ("pk", "trailsection_id", "name", "activity_ids")


class TrailSectionAdminSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    activities = TrailSectionActivitySerializer(many=True)

    class Meta:
        model = TrailSection
        fields = (
            "trailsection_id",
            "shape",
            "shape_2d",
            "name",
            "comments",
            "activities",
        )
        extra_kwargs = {
            "shape": {"read_only": True},
            "shape_2d": {
                "write_only": True,
                "required": True,
                "allow_null": False,
                "error_messages": {"required": _("Please provide a valid map data.")},
            },
        }

    def update_trailsection_activities(self, ts_uuid, activities_data):
        items_to_insert = []
        TrailsectionActivities.objects.filter(trailsection_uuid=ts_uuid).delete()
        for data in activities_data:
            items_to_insert.append(
                TrailsectionActivities(
                    trailsection_uuid=ts_uuid, activity_id=data["activity"].id
                )
            )

        if items_to_insert:
            TrailsectionActivities.objects.bulk_create(items_to_insert)

    def save_activities(self, instance, data):
        ids = []
        new_items = []

        for item in data:
            id = item.pop("id", None)
            if id:
                ids.append(id)
            else:
                item["trail_section"] = instance
                new_items.append(TrailSectionActivity(**item))

        instance.activities.exclude(id__in=ids).delete()
        if new_items:
            TrailSectionActivity.objects.bulk_create(new_items)

    def convert_3d_to_2d(self, shape_3d):
        wkt_w = WKTWriter()
        wkt_w.outdim = 2
        temp = wkt_w.write(shape_3d)
        return GEOSGeometry(temp)

    @transaction.atomic
    def create(self, validated_data):
        activities_data = validated_data.pop("activities")
        ts_uuid = str(uuid.uuid4())
        self.update_trailsection_activities(ts_uuid, activities_data)
        instance = self.Meta.model(**validated_data)
        instance.trailsection_activities_uuid = ts_uuid
        instance.save()
        self.save_activities(instance, activities_data)
        transaction.on_commit(lambda: call_command("remove_duplicate_trailsection"))
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        activities_data = validated_data.pop("activities")
        if "shape_2d" not in validated_data:
            raise serializers.ValidationError(
                {"shape_2d": _("Please provide a valid map data.")}
            )

        ts_uuid = str(uuid.uuid4())
        if not instance.trailsection_activities_uuid:
            instance.trailsection_activities_uuid = ts_uuid
        else:
            ts_uuid = instance.trailsection_activities_uuid

        self.update_trailsection_activities(ts_uuid, activities_data)
        self.save_activities(instance, activities_data)

        for key, value in validated_data.items():
            if key == "shape_2d" and value and value.hasz:
                value = self.convert_3d_to_2d(value)
            setattr(instance, key, value)

        instance.save()
        transaction.on_commit(lambda: call_command("remove_duplicate_trailsection"))
        return instance


class EventTrailSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTrailSection
        fields = ("trailsection", "start_position", "end_position", "order")


class TrailImageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    image_file = serializers.ImageField(source="image", write_only=True)

    class Meta:
        model = TrailImage
        fields = ("id", "image", "image_file", "image_type", "credit")
        extra_kwargs = {"image": {"read_only": True}}


class TrailStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrailStep
        fields = ("lat", "lng", "point", "order")


class TrailThinSerializer(serializers.ModelSerializer):
    activity_ids = serializers.ListField()

    class Meta:
        model = Trail
        fields = ("pk", "trail_id", "name", "activity_ids", "last_modified")


class TrailAdminSerializer(serializers.ModelSerializer):
    images = TrailImageSerializer(many=True, required=False)
    activities = TrailActivitySerializer(many=True)
    events = EventTrailSectionSerializer(write_only=True, many=True)
    steps = TrailStepSerializer(many=True, required=False)

    class Meta:
        model = Trail
        fields = (
            "trail_id",
            "name",
            "location",
            "path_type",
            "description",
            "activities",
            "images",
            "events",
            "steps",
        )
        extra_kwargs = {
            "name": {"required": True, "allow_blank": False},
            "location": {"required": True},
        }

    def update_images(self, instance, data):
        ids = []
        new_items = []

        for item in data:
            if "image_type" not in item:
                continue
            id = item.pop("id", None)
            if id:
                ids.append(id)
                TrailImage.objects.filter(id=id).update(**item)
            else:
                item["trail"] = instance
                new_items.append(TrailImage(**item))

        TrailImage.objects.filter(trail=instance).exclude(id__in=ids).delete()
        if new_items:
            TrailImage.objects.bulk_create(new_items)

    def save_activities(self, instance, data):
        ids = []
        new_items = []

        for item in data:
            id = item.pop("id", None)
            if id:
                ids.append(id)
            else:
                item["trail"] = instance
                new_items.append(TrailActivity(**item))

        instance.activities.exclude(id__in=ids).delete()
        for activity in new_items:
            activity.save()

    def save_events(self, instance, data):
        EventTrailSection.objects.filter(evnt_id=instance.pk).delete()
        new_items = []
        for item in data:
            item["evnt"] = instance.event
            new_items.append(EventTrailSection(**item))

        if new_items:
            EventTrailSection.objects.bulk_create(new_items)

    def save_steps(self, instance, data):
        instance.steps.all().delete()

        new_items = []
        for item in data:
            item["trail"] = instance
            new_items.append(TrailStep(**item))

        if new_items:
            TrailStep.objects.bulk_create(new_items)

    def update_shape(self, trail_id):
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

    def save_related(
        self, instance, activities_data, events_data, images_data, steps_data
    ):
        self.save_activities(instance, activities_data)
        self.save_events(instance, events_data)
        self.save_steps(instance, steps_data)
        self.update_images(instance, images_data)
        update_geometry_of_evenement.delay(instance.trail_id)

    @transaction.atomic
    def update(self, instance, validated_data):
        activities_data = validated_data.pop("activities")
        images_data = validated_data.pop("images", [])
        steps_data = validated_data.pop("steps", [])
        events_data = validated_data.pop("events")

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.hikster_creation = 4
        instance.save()
        self.save_related(
            instance, activities_data, events_data, images_data, steps_data
        )
        return instance

    @transaction.atomic
    def create(self, validated_data):
        activities_data = validated_data.pop("activities")
        steps_data = validated_data.pop("steps", [])
        events_data = validated_data.pop("events")
        images_data = validated_data.pop("images", [])
        instance = self.Meta.model(**validated_data)
        instance.hikster_creation = 4
        instance.save()
        self.save_related(
            instance, activities_data, events_data, images_data, steps_data
        )
        return instance
