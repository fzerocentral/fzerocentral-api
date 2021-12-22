"""
Django settings for this project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/

Deployment guidance
https://docs.djangoproject.com/en/dev/howto/deployment/checklist/
"""

from pathlib import Path

import environ


# Build paths like this: REPO_DIR / 'subdir'.
REPO_DIR = Path(__file__).resolve().parent.parent.parent.parent
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
SETTINGS_DIR = Path(__file__).resolve().parent


env = environ.Env()
# Read environment variables from the system or a .env file.
environ.Env.read_env(REPO_DIR / '.env')


# Generate a SECRET_KEY using:
# from django.core.management.utils import get_random_secret_key
# print(get_random_secret_key())
SECRET_KEY = env('SECRET_KEY')


# Applications that are enabled in this Django installation.
INSTALLED_APPS = [
    # Django REST framework
    'rest_framework',
    # JSON:API support for Django REST framework
    'rest_framework_json_api',

    'charts',
    'chart_groups',
    'games',
]

# The order of middleware classes is important.
# https://docs.djangoproject.com/en/dev/topics/http/middleware/
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'


# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        # If True, wraps each request (view function) in a transaction by
        # default. Individual view functions can override this behavior with
        # the non_atomic_requests decorator.
        'ATOMIC_REQUESTS': True,

        'NAME': env('DATABASE_NAME', default='fzerocentral'),
        'USER': env('DATABASE_USER', default='django'),
        'PASSWORD': env('DATABASE_PASSWORD'),
        # Set to empty string for localhost.
        'HOST': env('DATABASE_HOST', default=''),
        # Set to empty string for default.
        'PORT': env('DATABASE_PORT', default=''),
    }
}


# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Default primary key field type
# https://docs.djangoproject.com/en/dev/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Django REST Framework and DRF JSON API
# https://www.django-rest-framework.org/api-guide/settings/
# https://django-rest-framework-json-api.readthedocs.io/en/stable/usage.html#configuration

REST_FRAMEWORK = {
    # Set this to None so that we don't have to install the contenttypes and
    # auth apps yet.
    'UNAUTHENTICATED_USER': None,

    'PAGE_SIZE': 10,
    'EXCEPTION_HANDLER': 'rest_framework_json_api.exceptions.exception_handler',
    'DEFAULT_PAGINATION_CLASS':
        'rest_framework_json_api.pagination.JsonApiPageNumberPagination',
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework_json_api.parsers.JSONParser',
        # The below two parsers handle HTML form data; uncomment if useful.
        # Can also be enabled on a per-view basis.
        # 'rest_framework.parsers.FormParser',
        # 'rest_framework.parsers.MultiPartParser',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework_json_api.renderers.JSONRenderer',
    ),
    'DEFAULT_METADATA_CLASS': 'rest_framework_json_api.metadata.JSONAPIMetadata',
    'DEFAULT_SCHEMA_CLASS': 'rest_framework_json_api.schemas.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework_json_api.filters.OrderingFilter',
        # Advanced ORM-style filtering; uncomment if useful.
        # Can also be enabled on a per-view basis.
        # 'rest_framework_json_api.django_filters.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
    ),
    'SEARCH_PARAM': 'filter[search]',
    'TEST_REQUEST_RENDERER_CLASSES': (
        'rest_framework_json_api.renderers.JSONRenderer',
    ),
    'TEST_REQUEST_DEFAULT_FORMAT': 'vnd.api+json',
}

# How to format the field names returned in responses.
JSON_API_FORMAT_FIELD_NAMES = 'dasherize'
# How to format the resource 'type' returned in responses.
JSON_API_FORMAT_TYPES = 'dasherize'
# Pluralize the resource 'type' returned in responses.
JSON_API_PLURALIZE_TYPES = True
