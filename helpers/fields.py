# -*- coding: utf-8 -*-
import base64

from rest_framework import serializers
from rest_framework.fields import CharField


class DistanceField(serializers.Field):
    def to_internal_value(self, data):
        super(DistanceField, self).to_internal_value(data)

    def to_representation(self, value):
        return "{:.2f}".format(value.km)


class ContactField(CharField):
    def to_representation(self, value: str) -> str:
        if "mailto:" in value:
            return (value.split("mailto:"))[1].split("#")[0]
        elif "#" in value and value.count("#") > 1:
            return (value.split("#"))[1].split("#")[0]
        else:
            return value
