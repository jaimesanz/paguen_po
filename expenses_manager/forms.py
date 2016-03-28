# -*- coding: utf-8 -*-
from django import forms
from .models import *
from django.contrib.auth.models import User, Group

class UserForm(forms.ModelForm):
	password = forms.CharField(widget=forms.PasswordInput())

	class Meta:
		model = User
		fields = ('username', 'email', 'password')

class ViviendaForm(forms.ModelForm):
	class Meta:
		model = Vivienda
		fields = ('alias',)