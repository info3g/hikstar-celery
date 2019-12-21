import os
import random
import string

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _
from easy_thumbnails.fields import ThumbnailerImageField


class Address(models.Model):
    street_name = models.CharField(max_length=250, null=True, blank=True)
    apartment = models.CharField(default="", max_length=20, null=True, blank=True)
    city = models.CharField(max_length=250, null=True, blank=True)
    province = models.CharField(max_length=250, null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True)
    po_box = models.CharField(max_length=250, null=True, blank=True)
    country = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        street_city = []
        if self.street_name:
            street_city.append(self.street_name.strip())
        if self.city:
            street_city.append(self.city.strip())

        address = []
        if street_city:
            address.append(" ".join(street_city))
        if self.province:
            address.append(self.province.strip())
        if self.postal_code:
            address.append(self.postal_code.strip())
        if self.country:
            address.append(self.country.strip())

        return ", ".join(address)


class Document(models.Model):
    file = models.FileField(null=True, blank=True)


def generate_random_string(length=7):
    return "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(length)
    )


def get_image_upload_to(instance, filename):
    parent = getattr(instance, instance.parent_field)
    parent_id = getattr(parent, parent.id_field)
    ct = ContentType.objects.get_for_model(parent)
    ext = os.path.splitext(filename)[1]
    filename = "{}{}".format(generate_random_string(), ext.lower())

    path = "images/{}/{}/{}".format(ct.model, parent_id, filename)

    return path


class ImageBaseQuerySet(models.QuerySet):
    def banners(self, **kwargs):
        return self.filter(image_type="banner", **kwargs)


class ImageBase(models.Model):
    image_type = models.CharField(max_length=20)
    image = ThumbnailerImageField(max_length=300, upload_to=get_image_upload_to)
    credit = models.CharField(max_length=255, blank=True, null=True)
    old_image = models.CharField(max_length=256, null=True, blank=True)

    objects = ImageBaseQuerySet.as_manager()

    class Meta:
        abstract = True

    @property
    def dimensions(self):
        aliases = settings.THUMBNAIL_ALIASES[""]

        return aliases["standard"]["size"]

    def delete(self, **kwargs):
        self.image.delete(False)
        return super().delete(**kwargs)


class Contact(models.Model):
    TYPE_BLOG = "blog"
    TYPE_CELLULAR = "cellular"
    TYPE_EMAIL = "email"
    TYPE_FACEBOOK = "facebook"
    TYPE_FAX = "fax"
    TYPE_SITE = "site"
    TYPE_SITE_MOBILE = "site_mobile"
    TYPE_TELEPHONE = "telephone"
    TYPE_TELEPHONE_NO_CHARGE = "telephone_no_charge"
    TYPE_TELEPHONE_SECONDARY = "telephone_secondary"
    TYPE_TWITTER = "twitter"

    TYPE_CHOICES = (
        (TYPE_BLOG, _("Blog")),
        (TYPE_CELLULAR, _("Cellular")),
        (TYPE_EMAIL, _("Email")),
        (TYPE_FACEBOOK, _("Facebook")),
        (TYPE_FAX, _("Fax machine")),
        (TYPE_SITE, _("Site")),
        (TYPE_SITE_MOBILE, _("Site mobile")),
        (TYPE_TELEPHONE, _("Telephone")),
        (TYPE_TELEPHONE_NO_CHARGE, _("Telephone no charge")),
        (TYPE_TELEPHONE_SECONDARY, _("Telephone secondary")),
        (TYPE_TWITTER, _("Twitter")),
    )

    FRONTEND_TYPES = [
        TYPE_SITE,
        TYPE_TELEPHONE,
        TYPE_EMAIL,
    ]

    type = models.CharField(max_length=30, choices=TYPE_CHOICES, blank=True)
    value = models.CharField(max_length=250)

    def __str__(self):
        return "{0} : {1}".format(self.type, self.value)
