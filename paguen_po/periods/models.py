from django.db import models

# Create your models here.
from django.utils import timezone


def get_current_year_month_obj():
    """
    Returns the current YearMonth period.
    If the YearMonth doesn't exist, it creates it.
    :return: YearMonth
    """
    today = timezone.now()
    year_month, created = YearMonth.objects.get_or_create(
        year=today.year, month=today.month)
    return year_month


def get_current_year_month():
    """
    Returns the current YearMonth period's ID field.
    If it doesn't exist, it creates it.
    :return: Integer
    """
    return get_current_year_month_obj().id


class YearMonth(models.Model):

    class Meta:
        unique_together = (('year', 'month'),)
    year = models.IntegerField()
    month = models.IntegerField()

    def get_next_period(self):
        """
        Returns a Tuple of Integers with:
        - the year of the period following this YearMonth
        - the month of the period following this YearMonth
        :return: Pair( Integer, Integer )
        """
        next_month = self.month + 1
        next_year = self.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        return (next_year, next_month)

    def get_prev_period(self):
        """
        Returns a Tuple of Integers with:
        - the year of the period previous to this YearMonth
        - the month of the period previous to this YearMonth
        :return: Pair( Integer, Integer )
        """
        prev_month = self.month - 1
        prev_year = self.year
        if prev_month == 0:
            prev_month = 12
            prev_year -= 1
        return (prev_year, prev_month)

    def __str__(self):
        return str(self.year) + "-" + str(self.month)