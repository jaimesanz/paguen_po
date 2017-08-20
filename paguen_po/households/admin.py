from django.contrib import admin

from .models import Household, Roommate


class HouseholdRoommateInline(admin.TabularInline):
    model = Household.users.through
    extra = 0


class HouseholdAdmin(admin.ModelAdmin):
    inlines = (HouseholdRoommateInline,)


admin.site.register(Household, HouseholdAdmin)
admin.site.register(Roommate)
