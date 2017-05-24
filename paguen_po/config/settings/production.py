# -*- coding: utf-8 -*-
from .base import *

ALLOWED_HOSTS = ["*"]

DEBUG = False

EMAIL_BACKEND = "django_ses.SESBackend"
DEFAULT_FROM_EMAIL = get_secret("default_from_email")
EMAIL_HOST = ''

AWS_ACCESS_KEY_ID = get_secret("aws_access_key_id")
AWS_SECRET_ACCESS_KEY = get_secret("aws_secret_access_key")

X_FRAME_OPTIONS = "DENY"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 3600

SECURE_HSTS_INCLUDE_SUBDOMAINS = True
