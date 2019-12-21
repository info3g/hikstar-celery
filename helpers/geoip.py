import requests
from django.conf import settings
from django.contrib.gis.geos.point import Point


API_URL_TEMPLATE = "http://api.ipstack.com/{}?access_key={}"


class ReverseGeoIPClient:
    def get_location_from_ip(self, ip):
        url = API_URL_TEMPLATE.format(ip, settings.IPSTACK_KEY)
        response = requests.get(url)
        data = response.json()
        return Point(data['latitude'], data['longitude'])
