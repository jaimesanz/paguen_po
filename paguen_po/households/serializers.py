# -*- coding: utf-8 -*-
from rest_framework import serializers
from .models import Household


class HouseholdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Household
        fields = ('id', 'name')
