# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


class Vivienda(models.Model):
	alias = models.CharField(max_length=200)
	def __unicode__(self):
		return self.alias

class ViviendaUsuario(models.Model):
	class Meta:
		unique_together = (('vivienda', 'user'),)
	vivienda = models.ForeignKey(Vivienda, on_delete=models.CASCADE)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	def __unicode__(self):
		return self.vivienda + "__" + self.user

class Invitacion(models.Model):
	# this key can be null if you invite an account-less user. In this case the invitation is sent to the email.
	invitado = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
	invitado_por = models.ForeignKey(ViviendaUsuario, on_delete=models.CASCADE)
	email = models.EmailField()

	def __unicode__(self):
		return self.invitado + "__invited__" + self.invitado_por
