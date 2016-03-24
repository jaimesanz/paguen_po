# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


class Vivienda(models.Model):
	alias = models.CharField(max_length=200)
	def __unicode__(self):
		return self.alias

class Usuario(models.Model):
	# This line is required. Links Usuario to a Django User model instance.
	user_id = models.OneToOneField(User)

	# The additional attributes we wish to include.
	alias = models.CharField(max_length=200)

	# Override the __unicode__() method to return out something meaningful!
	def __unicode__(self):
		return self.alias
