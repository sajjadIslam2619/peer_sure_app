"""
WSGI config for peer_sure_app project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import logging
#from .settings import DJANGO_ENV
logger = logging.getLogger(__name__)
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'peer_sure_app.settings')

application = get_wsgi_application()

DJANGO_ENV = os.getenv('DJANGO_ENV_PEER_SURE', 'dev')
logger.info(f'Deployment Environment :: {DJANGO_ENV}')