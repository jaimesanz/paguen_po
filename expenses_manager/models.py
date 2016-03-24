from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Vivienda(models.Model):
	alias = models.CharField(max_length=200)