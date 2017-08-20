# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Expense, Category


class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('amount', 'category', 'roommate', 'year', 'month')

admin.site.register(Expense, ExpenseAdmin)
admin.site.register(Category)
