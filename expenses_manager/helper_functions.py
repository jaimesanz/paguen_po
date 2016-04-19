def get_next_year_month_pair(y, m):
    next_year = y
    next_month = m + 1
    if next_month > 12:
        next_month = 1
        next_year += 1
    return (next_year, next_month)


def get_periods(y0, m0, y1, m1):
    periods = []
    y = y0
    m = m0
    while y < y1 or (y <= y1 and m <= m1):
        periods.append((y, m))
        y, m = get_next_year_month_pair(y, m)
    return periods


def is_valid_year_month_range(y0, m0, y1, m1):
    return True
