from rest_framework import serializers

from hikster.helpers.fields import ContactField
from .models import Address, Contact, ImageBase


class AddressSerializer(serializers.ModelSerializer):
    formatted = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Address
        fields = "__all__"

    def get_formatted(self, obj):
        return str(obj)


class ContactSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    value = ContactField()

    class Meta:
        model = Contact
        fields = "__all__"


class ImageSerializerBase(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    dimensions = serializers.ReadOnlyField()

    def get_image(self, instance: ImageBase):
        return instance.image["standard"].url
