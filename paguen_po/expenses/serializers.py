# -*- coding: utf-8 -*-
from rest_framework import serializers

from households.serializers import RoommateSerializer

from .models import Category, Expense


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('id', 'name')


class ExpenseSerializer(serializers.ModelSerializer):
    roommate = RoommateSerializer(read_only=True)

    class Meta:
        model = Expense
        fields = ('amount', 'category', 'roommate', 'year', 'month')
