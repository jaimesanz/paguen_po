# -*- coding: utf-8 -*-
from rest_framework import generics

from .serializers import HouseholdSerializer


class HouseholdList(generics.ListCreateAPIView):
    """Lists all households for a given user."""
    serializer_class = HouseholdSerializer

    def get_queryset(self):
        """
        This view should return a list of all the purchases
        for the currently authenticated user.
        """
        user = self.request.user
        return user.household_set.all()
