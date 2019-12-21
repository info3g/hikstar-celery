import os
import logging

from django.core.wsgi import get_wsgi_application
from whitenoise.django import DjangoWhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hikster.settings')
application = get_wsgi_application()
application = DjangoWhiteNoise(application)

logger = logging.getLogger('hikster')
logger.info('app_ready')
