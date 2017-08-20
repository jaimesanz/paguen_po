# -*- coding: utf-8 -*-
from rest_framework import generics
from rest_framework import permissions

from households.models import Roommate

from .models import Category, Expense
from .serializers import CategorySerializer, ExpenseSerializer


class CategoryList(generics.ListCreateAPIView):
    """Lists all Categories or creates a new one."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (permissions.IsAuthenticated,)


class ExpensesList(generics.ListAPIView):
    """Lists all expenses for a given Household"""
    serializer_class = ExpenseSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """This view should return a list of all the expense for the currently authenticated user's
        household.
        """
        household = self.request.query_params.get('household', None)
        if household is not None and Roommate.objects.filter(
                user=self.request.user, household_id=household).exists():
            return Expense.objects.filter(roommate__household_id=household)
        return Expense.objects.none()
