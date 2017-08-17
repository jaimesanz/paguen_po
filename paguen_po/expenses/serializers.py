# -*- coding: utf-8 -*-
from rest_framework import serializers
from .models import Category, Expense


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('id', 'name')


class ExpenseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Expense
        fields = ('amount', 'category', 'user', 'year', 'month')
