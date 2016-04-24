from django.contrib import messages


def get_next_year_month_pair(y, m):
    """
    Takes 2 integers representing a Year and a Month.
    Returns the pair of Integers representing the next month from that period.
    If the month overflows (>12) it adds another year.
    """
    next_year = y
    next_month = m + 1
    if next_month > 12:
        next_month = 1
        next_year += 1
    return (next_year, next_month)


def get_periods(y0, m0, y1, m1):
    """
    Takes 4 integers representing 2 periods. The first and second argument
    represent the starting period, and the 3rd and 4rth arguments represent
    the final period. Return a list of tuples with all periods between
    the starting and end periods, including them.
    """
    periods = []
    y = y0
    m = m0
    while y < y1 or (y <= y1 and m <= m1):
        periods.append((y, m))
        y, m = get_next_year_month_pair(y, m)
    return periods


def is_valid_year_month_range(y0, m0, y1, m1):
    """
    Returns True only if the period corresponding to y1,m1 is a date that comes
    after  the period corresponding to y0,m0.
    """
    return (y0 < y1) or (y0 == y1 and m0 <= m1)


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
