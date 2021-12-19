# Settings for a development server.

from .base import *


DEBUG = True

# Host/domain names that this Django site can serve. This is a security
# measure to prevent HTTP Host header attacks.
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
#
# When DEBUG is True and ALLOWED_HOSTS is empty, the host is validated
# against ['.localhost', '127.0.0.1', '[::1]'].
ALLOWED_HOSTS = []

# No HTTPS.
SECURE_PROXY_SSL_HEADER = None
