# -*- coding: utf-8 -*-
from .base import *

ALLOWED_HOSTS = ["*"]

AWS_ACCESS_KEY_ID = get_secret("aws_access_key_id")
AWS_SECRET_ACCESS_KEY = get_secret("aws_secret_access_key")
