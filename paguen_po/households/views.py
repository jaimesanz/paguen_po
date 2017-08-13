# -*- coding: utf-8 -*-
from rest_framework import generics

from .models import Household
from .serializers import HouseholdSerializer


class HouseholdList(generics.ListCreateAPIView):
    queryset = Household.objects.all()
    serializer_class = HouseholdSerializer
