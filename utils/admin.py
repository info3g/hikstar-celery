from django.contrib.gis import admin
from .models import Address, Contact


admin.site.register((Address, Contact), )
