from django.core.urlresolvers import resolve, reverse
from django.test import TestCase
from django.http import HttpRequest
from django.template.loader import render_to_string

class DummyTest(TestCase):
	def test_dummy(self):
		pass