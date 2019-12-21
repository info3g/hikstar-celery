from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator


def is_email(value: str):
    validator = EmailValidator()
    try:
        validator(value)
    except ValidationError:
        return False

    return True


def is_url(url):
  try:
    result = urlparse(url)
    return all([result.scheme, result.netloc])
  except ValueError:
    return False
