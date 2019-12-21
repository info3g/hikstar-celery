from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from hikster.utils.serializers import AddressSerializer
from .models import Organization


class ValidateWidgetSerializer(serializers.Serializer):
    token = serializers.CharField()
    locations = serializers.CharField(required=False, allow_blank=True)

    def validate_token(self, value):
        try:
            org = Organization.objects.get(aid=value)

            if not org.locations.exists():
                raise serializers.ValidationError(
                    _("Organization has no location."), code="org_no_location"
                )
        except Organization.DoesNotExist:
            raise serializers.ValidationError(_("Invalid token"), code="invalid_token")

        return org

    def validate(self, data):
        locations = data.get("locations", "").strip()
        org_locations = data["token"].locations.all()
        if locations:
            try:
                location_ids = list(map(int, locations.split(",")))
            except (AttributeError, ValueError):
                raise serializers.ValidationError(
                    {
                        "locations": _(
                            "Invalid locations value. Please provide a comma separated location ids."
                        )
                    },
                    code="invalid_locations",
                )
            org_locations = org_locations.filter(location_id__in=location_ids)

        if not org_locations:
            raise serializers.ValidationError(
                {"locations": _("Locations not found in organization.")},
                code="location_not_found",
            )

        return data


class UserThinSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)

    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name", "email")


class OrganizationSerializer(serializers.ModelSerializer):
    address = AddressSerializer()

    class Meta:
        model = Organization
        fields = "__all__"


class OrgWithUserSerializer(OrganizationSerializer):

    user = UserThinSerializer(write_only=True)

    @transaction.atomic
    def update(self, instance, validated_data):
        address_data = validated_data.pop("address")
        address_serializer = AddressSerializer(instance.address, address_data)
        address_serializer.is_valid(raise_exception=True)
        address_serializer.save()

        user_data = validated_data.pop("user", None)

        if user_data is not None and self.context["request"]:
            user = self.context["request"].user
            user_serializer = UserThinSerializer(user, user_data)
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()
        return instance
