"""
WSGI config for this Django project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/
"""

import os

from django.core.exceptions import ImproperlyConfigured
from django.core.wsgi import get_wsgi_application

# We could potentially assume that this WSGI app only gets used by production.
# However, development environments also have to specify the settings module,
# so we'll make production specify that too, for consistency.
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    raise ImproperlyConfigured(
        "Must set the DJANGO_SETTINGS_MODULE environment variable."
        " Example value: config.settings.production")

application = get_wsgi_application()
