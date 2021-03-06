"""
Django settings for project_root project.

Generated by 'django-admin startproject' using Django 1.9.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""
# -*- coding: utf-8 -*-
import os
import json

from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# JSON-based secrets module
with open(os.path.join(BASE_DIR, 'config', 'secrets.json')) as f:
    secrets = json.loads(f.read())


# get the secret variables using this method
def get_secret(setting, secrets=secrets):
    """Get the secret variable or return explicit exception."""
    try:
        return secrets[setting]
    except KeyError:
        error_msg = "Set the {0} variable in secrets file.".format(setting)
        raise ImproperlyConfigured(error_msg)

SECRET_KEY = get_secret('secret_key')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'django.contrib.humanize',
    'rest_framework',
    'django_js_reverse',
    'core',
    'expenses',
    'households'
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                "django.template.context_processors.media",
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': get_secret("db_name"),
        'USER': get_secret("db_user"),
        'PASSWORD': get_secret("db_pass"),
        'HOST': get_secret("db_host"),
        'PORT': get_secret("db_port"),
        'TEST': {
            'NAME': 'mytestdatabase',
        }
    }
}
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LOGIN_URL = '/accounts/login/'

ACCOUNT_ACTIVATION_DAYS = 7  # One-week activation window;
LOGIN_REDIRECT_URL = '/login_post_process/'

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'es-cl'

TIME_ZONE = 'America/Santiago'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# TODO this is hardcoded to match:
# - the date format in static/js/jquery.ui.datepicker-es
# - the way django prints a timezone instance. For example,
# print(timezone.now().date()) prints something like "2016-9-26". Because
# of this, if the format is changed, the tests won't pass, since django prints
# dates in this format. Can this be changed?
# Question: Is it posible to match jqueryUI datepicker,
# datetime's strptime and the way python prints dates with no harcoding
# involved? ie, just using the magic of locale?
DATE_FORMAT = "%Y-%m-%d"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, 'static_root'))

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

JS_REVERSE_OUTPUT_PATH = os.path.join(BASE_DIR, 'static_src')
JS_REVERSE_JS_GLOBAL_OBJECT_NAME = 'window'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

NOSE_ARGS = ['--nocapture', '--nologcapture', ]

CRISPY_TEMPLATE_PACK = 'bootstrap3'

# email configuration values for Gmail
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
# gmail account info
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
DEFAULT_FROM_EMAIL = ''
# DEFAULT_TO_EMAIL = 'to email'

FIXTURE_DIRS = (
    os.path.join(BASE_DIR, 'fixtures'),
)
