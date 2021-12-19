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


# Django REST Framework
# https://www.django-rest-framework.org/api-guide/settings/
REST_FRAMEWORK = {
    # Set this to None so that we don't have to install the contenttypes and
    # auth apps yet.
    'UNAUTHENTICATED_USER': None,

    # Some APIs have multiple rendering methods available, but for simplicity
    # we'll just have JSON API rendering.
    'DEFAULT_RENDERER_CLASSES': [
        'core.renderers.JSONAPIRenderer',
    ],
}
