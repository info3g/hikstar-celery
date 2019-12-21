from expander import ExpanderSerializerMixin
from rest_framework import serializers

from hikster.helpers import fields
from hikster.helpers import mixins, functions
from hikster.utils.models import Contact
from hikster.utils.serializers import (
    ImageSerializerBase,
    ContactSerializer,
    AddressSerializer,
)
from .models import (
    Location,
    LocationImage,
    PointOfInterestType,
    PointOfInterest,
    PointOfInterestImage,
)


class LocationImageSerializer(ImageSerializerBase):
    class Meta:
        model = LocationImage
        exclude = ["id", "location"]


class LocationSerializer(
    ExpanderSerializerMixin,
    mixins.ExcludeFieldsMixin,
    mixins.IncludeFieldsMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(source="location_id", required=False, read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name="location-detail", read_only=True
    )
    object_type = serializers.ReadOnlyField()
    distance = fields.DistanceField(read_only=True)

    class Meta:
        model = Location
        fields = "__all__"
        expandable_fields = {
            "address": AddressSerializer,
            "contact": (ContactSerializer, (), {"many": True}),
            "images": (LocationImageSerializer, (), {"many": True}),
        }
        extra_kwargs = {
            "address": {"allow_null": True, "required": False},
            "contact": {"allow_null": True, "required": False},
            "images": {"allow_null": True, "required": False},
        }

    def validate_type(self, value):
        if value not in list(range(7, 11 + 1)):
            raise serializers.ValidationError(
                "Ce lieu n'a pas de catégorie ou celle-ci n'est pas valide."
            )
        return value

    def create(self, validated_data):
        address = validated_data.pop("address", None)
        contacts = validated_data.pop("contact", None)
        images = validated_data.pop("images", None)

        # We save the new location as usual
        location = super(LocationSerializer, self).create(validated_data)

        if address:
            location.address = functions.save_nested(address, AddressSerializer)

        location.save()

        # We get the user from the context request so we can add the new object to it
        user = self.context["request"].user.trailadmin
        location.owner.add(user)

        if contacts:
            location.contact = functions.save_nested(contacts, ContactSerializer)
        if images:
            location.images = functions.save_nested(images, LocationImageSerializer)

        return location

    def update(self, instance: Location, validated_data):
        address = validated_data.pop("address", None)
        contacts = validated_data.pop("contact", None)
        images = validated_data.pop("images", None)

        for key, value in validated_data.items():
            setattr(instance, key, value)

        # Save foreign key related fields
        if address:
            instance.address = functions.save_nested(address, AddressSerializer)

        # Save before doing shenanigans with relationships
        instance.save()

        # Save m2m related field
        if contacts:
            if not instance.contact.exists():
                instance.contact = functions.save_nested(contacts, ContactSerializer)
            else:
                existing_contacts = set(instance.contact.values_list("id", flat=True))
                contacts_to_update = set(
                    [contact["id"] for contact in contacts if "id" in contact]
                )

                instance.contact.filter(
                    id__in=existing_contacts - contacts_to_update
                ).delete()

                for contact in contacts:
                    new_contact = Contact(**contact)
                    new_contact.save()
                    instance.contact.add(new_contact)
        else:
            instance.contact.all().delete()

        if images:
            if not instance.images.all().exists():
                instance.images = functions.save_nested(images, LocationImageSerializer)
            else:
                # We need to delete the image removed from the interface
                # We do this by doing a diff of the existing images and the one to save
                # We're left with only the images to remove (the ones that are not present in the passed array)
                existing_img = set(instance.images.values_list("id", flat=True))
                img_to_update = set([image["id"] for image in images if "id" in image])

                # If the ids are in the the remainder of the diff between the existing img and the img to update
                # it means we've deleted it in the ui
                instance.images.filter(id__in=existing_img - img_to_update).delete()

                # We save the new images as usual, which equals to adding it to the existing ones after clearing the

                for image in images:
                    img = LocationImage(**image)
                    img.save()
                    instance.images.add(img)
        else:
            instance.images.all().delete()
        return instance


class LimitedLocationSerializer(LocationSerializer):
    class Meta:
        model = Location
        fields = ("id", "name")


class PointOfInterestTypeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = PointOfInterestType


class PointOfInterestImageSerializer(ImageSerializerBase):
    class Meta:
        model = PointOfInterestImage
        exclude = ["id", "location"]


class PointOfInterestSerializer(
    ExpanderSerializerMixin,
    mixins.ExcludeFieldsMixin,
    mixins.IncludeFieldsMixin,
    serializers.ModelSerializer,
):
    object_type = serializers.ReadOnlyField()
    distance = fields.DistanceField(read_only=True)

    class Meta:
        model = PointOfInterest
        fields = "__all__"
        expandable_fields = {
            "address": AddressSerializer,
            "contact": (ContactSerializer, (), {"many": True}),
            "images": (PointOfInterestImageSerializer, (), {"many": True}),
            "location": (LocationSerializer, (), {"many": True}),
            "type": PointOfInterestTypeSerializer,
        }
