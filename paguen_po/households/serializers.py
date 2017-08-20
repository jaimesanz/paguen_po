# -*- coding: utf-8 -*-
from rest_framework import serializers
from .models import Household, Roommate


class HouseholdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Household
        fields = ('id', 'name')


class RoommateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roommate
        fields = ('household', 'user')
