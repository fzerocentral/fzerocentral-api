# Settings for a production server.

from .base import *


DEBUG = False

# Host/domain names that this Django site can serve. This is a security
# measure to prevent HTTP Host header attacks.
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [env('SITE_HOST')]

# Use HTTPS.
# This setting is needed if we have an nginx config that connects to Django
# with a non-HTTPS proxy_pass.
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

WSGI_APPLICATION = 'config.wsgi.application'


# https://docs.djangoproject.com/en/dev/topics/logging/
# https://docs.djangoproject.com/en/dev/ref/logging/
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': env('LOG_PATH'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
