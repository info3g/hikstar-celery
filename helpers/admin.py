from django.contrib.gis import admin as gis_admin
from django.forms.widgets import Textarea


class HiksterGeoAdmin(gis_admin.OSMGeoAdmin):
    widget = Textarea


class SecureOSM(HiksterGeoAdmin):
    openlayers_url = 'https://cdn.jsdelivr.net/openlayers/2.13.1/OpenLayers.js'
