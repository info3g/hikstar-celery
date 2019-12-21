# -*- coding: utf-8 -*-


def create_image():
    import base64
    import requests

    response = requests.get('http://www.engraversnetwork.com/files/placeholder.jpg')
    uri = ("data:" +
           response.headers['Content-Type'] + ";" +
           "base64," + str(base64.b64encode(response.content).decode("utf-8")))
    return uri
