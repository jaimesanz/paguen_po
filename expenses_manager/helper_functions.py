from django.contrib import messages
from .models import Categoria


def create_new_vivienda(form):
    new_viv = form.save()
    # add global categorias
    categorias_globales = Categoria.objects.filter(vivienda=None)
    for cat in categorias_globales:
        Categoria.objects.create(
            nombre=cat.nombre,
            vivienda=new_viv)
    return new_viv


def get_next_year_month_pair(year, month):
    """
    Takes 2 integers representing a Year and a Month.
    Returns the pair of Integers representing the next month from that period.
    If the month overflows (>12) it adds another year.
    """
    next_year = year
    next_month = month + 1
    if next_month > 12:
        next_month = 1
        next_year += 1
    return (next_year, next_month)


def get_periods(year0, month0, year1, month1):
    """
    Takes 4 integers representing 2 periods. The first and second argument
    represent the starting period, and the 3rd and 4rth arguments represent
    the final period. Return a list of tuples with all periods between
    the starting and end periods, including them.
    """
    periods = []
    year = year0
    month = month0
    while year < year1 or (year <= year1 and month <= month1):
        periods.append((year, month))
        year, month = get_next_year_month_pair(year, month)
    return periods


def is_valid_year_month_range(year0, month0, year1, month1):
    """
    Returns True only if the period corresponding to year1,month1 is a
    date that comes after the period corresponding to year0,month0.
    """
    return (year0 < year1) or (year0 == year1 and month0 <= month1)


def user_has_vivienda(request):
    """
    If the user contained in the request belongs to a Vivienda, it returns
    True. If not, it returns False, and appends and error message
    to the request
    """
    if not request.user.has_vivienda():
        messages.error(
            request,
            "Para tener acceso a esta página debe pertenecer a una vivienda")
        return False
    return True
