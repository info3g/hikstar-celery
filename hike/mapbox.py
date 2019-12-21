from mapbox import Geocoder


def get_location_from_name(name):
    geocoder = Geocoder(access_token="pk.eyJ1IjoiY2xhaXJlZGVndWVsbGUiLCJhIjoiY2pnM3N1a3llMmF1azJxbnk3dm13dWptbCJ9.6T1hh6p4-bU-wrE-fVTSxQ")

    mapbox_response = geocoder.forward(name)
    if len(mapbox_response.geojson()['features']) == 0:
        return None

    location = mapbox_response.geojson()['features'][0]['geometry']

    return location
