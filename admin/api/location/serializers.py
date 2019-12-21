from django.db import transaction

from rest_framework import serializers

from hikster.location.models import (
    Location,
    LocationImage,
    PointOfInterest,
    PointOfInterestImage,
)
from hikster.utils.models import Contact
from hikster.utils.serializers import AddressSerializer, ContactSerializer


class AddressMixin(object):
    def save_address(self, instance, address_data):
        if instance.address:
            address_serializer = AddressSerializer(instance.address, data=address_data)
        else:
            address_serializer = AddressSerializer(data=address_data)

        if instance.address or address_data:
            address_serializer.is_valid(raise_exception=True)
            instance.address = address_serializer.save()
            instance.save()


class ContactMixin(object):
    def save_contact(self, instance, contact_data):
        contact_ids = []
        for c_data in contact_data:
            c_id = c_data.pop("id")
            if c_id:
                contact = Contact.objects.get(id=c_id)
                contact_serializer = ContactSerializer(contact, data=c_data)
            else:
                contact_serializer = ContactSerializer(data=c_data)

            contact_serializer.is_valid(raise_exception=True)
            contact = contact_serializer.save()
            contact_ids.append(contact.id)
            instance.contact.add(contact)

        instance.contact.exclude(id__in=contact_ids).delete()


class ImageMixin(object):
    image_model = None

    def delete_images(self, instance, ids):
        pass

    def update_images(self, instance, data):
        ids = []
        new_items = []

        for item in data:
            if "image_type" not in item:
                continue
            id = item.pop("id", None)
            if id:
                ids.append(id)
                self.image_model.objects.filter(id=id).update(**item)
            else:
                item["location"] = instance
                new_items.append(LocationImage(**item))

        self.delete_images(instance, ids)
        if new_items:
            self.image_model.objects.bulk_create(new_items)


class BaseImageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    image_file = serializers.ImageField(source="image", write_only=True)


class LocationImageSerializer(BaseImageSerializer):
    class Meta:
        model = LocationImage
        fields = ("id", "image", "image_file", "image_type", "credit")
        extra_kwargs = {"image": {"read_only": True}}


class POIImageSerializer(BaseImageSerializer):
    class Meta:
        model = PointOfInterestImage
        fields = ("id", "image", "image_file", "image_type", "credit")
        extra_kwargs = {"image": {"read_only": True}}


class LocationAdminSerializer(
    serializers.ModelSerializer, AddressMixin, ContactMixin, ImageMixin
):
    address = AddressSerializer()
    contact = ContactSerializer(many=True)
    images = LocationImageSerializer(many=True)
    image_model = LocationImage

    class Meta:
        model = Location
        fields = "__all__"

    def delete_images(self, instance, ids: list):
        LocationImage.objects.filter(location=instance).exclude(id__in=ids).delete()

    @transaction.atomic
    def update(self, instance, validated_data):
        images_data = validated_data.pop("images")
        address_data = validated_data.pop("address")
        contact_data = validated_data.pop("contact")

        self.update_images(instance, images_data)
        self.save_address(instance, address_data)
        self.save_contact(instance, contact_data)

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()
        return instance


class POIAdminThinSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = PointOfInterest
        fields = ("poi_id", "name", "display_name", "date_modified")


class POIAdminSerializer(
    serializers.ModelSerializer, AddressMixin, ContactMixin, ImageMixin
):
    address = AddressSerializer()
    contact = ContactSerializer(many=True, required=False)
    images = POIImageSerializer(many=True, required=False)
    image_model = PointOfInterestImage

    class Meta:
        model = PointOfInterest
        fields = (
            "poi_id",
            "name",
            "shape",
            "description",
            "fare",
            "category",
            "type",
            "address",
            "contact",
            "images",
        )
        extra_kwargs = {
            "category": {"required": True},
            "name": {"required": True},
            "shape": {"required": True},
            "type": {"required": True},
        }

    def delete_images(self, instance, ids: list):
        PointOfInterestImage.objects.filter(location=instance).exclude(
            id__in=ids
        ).delete()

    @transaction.atomic
    def update(self, instance, validated_data):
        images_data = validated_data.pop("images", [])
        address_data = validated_data.pop("address")
        contact_data = validated_data.pop("contact")

        self.update_images(instance, images_data)

        self.save_address(instance, address_data)
        self.save_contact(instance, contact_data)

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()
        return instance

    @transaction.atomic
    def create(self, validated_data):
        images_data = validated_data.pop("images", [])
        address_data = validated_data.pop("address")
        contact_data = validated_data.pop("contact")
        validated_data.update(
            {"premium": True, "position_quality": True, "visible_in_map": 1}
        )
        instance = self.Meta.model(**validated_data)
        instance.save()

        self.update_images(instance, images_data)
        self.save_address(instance, address_data)
        self.save_contact(instance, contact_data)
        return instance
