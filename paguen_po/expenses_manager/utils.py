# -*- coding: utf-8 -*-
from django.contrib import messages

import xlwt

from expenses_manager.models import Categoria, ProxyUser


def rm_not_active_at_date(user_set, date):
    """
    Given a set of ViviendaUsuario instances and a date, returns a
    subset of the original set with all ViviendaUsuario instances
    that were active at the given date
    :param user_set: Set(ViviendaUsuario)
    :param date: Timezone Date instance
    :return: Set(ViviendaUsuario)
    """
    active_at_date = set()
    for vu in user_set:
        joined_before = vu.fecha_creacion <= date
        fecha_left = vu.fecha_abandono
        left_after = fecha_left is None or fecha_left >= date
        if joined_before and left_after:
            active_at_date.add(vu)
    return active_at_date


def rm_users_out_at_date(user_set, vacations, date):
    """
    Given a set of ViviendaUsuario instances and a dict with the
    ViviendaUsuario's vacations, returns a subset of the original set
    of ViviendaUsuario with all instances that were active and not on
    vacation at the given date
    :param user_set: Set(ViviendaUsuario)
    :param vacations: Set(UserIsOut)
    :param date: Timezone Date instance
    :return: Set(ViviendaUsuario)
    """
    users_on_vac = set()
    for vu in user_set:
        for vac in vacations.get(vu, []):
            gasto_after = date >= vac.fecha_inicio
            gasto_before = date <= vac.fecha_fin
            if gasto_after and gasto_before:
                users_on_vac.add(vu)
    # these are the users that don't have to pay
    return user_set - users_on_vac


def get_pos_neg_dicts_from_balance(balance):
    """
    Given a disbalance dict, returns a dict with only those users that
    have a positive balance (have spent too much) and another dict only
    with users that have a negative balance (have spent too little)
    :param balance: dict(User -> Integer)
    :return: Tuple(dict(User -> Integer), dict(User -> Integer))
    """
    pos = dict()
    neg = dict()
    for user, diff in balance.items():
        if diff > 0:
            pos[user] = diff
        elif diff < 0:
            neg[user] = abs(diff)
        else:
            # user is exactly at 0
            pass
    return pos, neg


def get_instructions_from_pos_neg(pos, neg):
    """
    Generates the instructions to balance out the expenses of the
    Vivienda's Users
    :param neg: dict(User: Integer)
    :param pos: dict(User: Integer)
    :return: dict(User: List( Pair( User, Integer ) )
    """
    transfers = dict()
    for neg_user, neg_total in neg.items():
        transfers[neg_user] = list()
        this_transfer = neg_total
        for pos_user, pos_total in pos.items():
            if this_transfer == 0:
                break
            # neg_user must transfer as much as he can to pos_user,
            # but without transferring more than pos_total.
            transfer_monto = min(this_transfer, pos_total)
            if transfer_monto>0:
                transfers[neg_user].append((pos_user, transfer_monto))
                pos[pos_user] -= transfer_monto
                this_transfer -= transfer_monto
    return transfers


def get_instructions_from_balance(balance):
    """
    Generates the instructions for the users to balance out their shared
    expenses.
    :param balance: dict(User: Integer)
    :return: dict(User: List( Pair( User, Integer ) )
    """
    pos, neg = get_pos_neg_dicts_from_balance(balance)
    # users who have spent too little must transfer to users that have
    # spent too much
    instr = get_instructions_from_pos_neg(pos, neg)
    return instr


def compute_balance(actual, expected):
    """
    "actual" represents how much a user has actually spent.
    "expected" represents how much each User should have spent.
    Both dicts must have the same Keys.
    Returns a dict where each tuple represents how much the Key-User has
    to transfer to the Tuple-User so that everyone ends up spending the
    same.
    :param actual: dict(User: Integer)
    :param expected: dict(User: Integer)
    :return: Dict(User: List( Pair( User, Integer ) )
    """
    balance = get_balance_from_totals(actual, expected)
    if balance is not None:
        # compute dict for users with positive balance (has spent too
        # much) and dict for users with negative balance (has spent too
        # little)
        return get_instructions_from_balance(balance)
    else:
        return None


def get_balance_from_totals(actual, expected):
    """
    Computes the balance based on the actual totals and the expected totals
    per user
    :param actual: dict(User: Integer)
    :param expected: dict(User: Integer)
    :return: dict(User: Integer)
    """
    # check that dicts are valid:
    same_keys = set(actual.keys()) == set(expected.keys())
    same_sum = sum(actual.values()) == sum(actual.values())
    if same_keys and same_sum:
        balance = dict()
        for user, act in actual.items():
            exp = expected.get(user)
            balance[user] = act - exp
        return balance
    else:
        return None


def add_row(ws, row_index, elements, style=xlwt.XFStyle()):
    """
    Given a list of elements to write and a row index, writes all elements in
    said row, in order. Creates a column per element.
    :param ws: XLWT worksheet
    :param row_index: Integer
    :param elements: List( String )
    :param style: XLWT style
    :return: None
    """
    for idx, e in enumerate(elements):
        ws.write(row_index, idx, str(e), style)


def add_header(ws, elements):
    """
    Adds first row to worksheet using XLWT styles.
    :param ws: empty XLWT worksheet
    :param elements: List( String )
    :return: None
    """
    style = xlwt.easyxf('pattern: pattern solid, fore_colour light_blue;'
                        'font: colour white, bold True;')
    add_row(ws, 0, elements, style)


def write_gastos_to_xls_sheet(ws, gastos):
    """
    For each gasto in gastos parameter, adds a new row to the worksheet.
    :param ws: empty XLWT Worksheet
    :param gastos: List( Gasto )
    :return: Integer
    """
    add_header(ws, get_gasto_headers())
    for idx, gasto in enumerate(gastos):
        add_row(ws, idx + 1, get_gasto_row_data(gasto))


def get_gasto_headers():
    """
    Returns the headers for a Gasto XLS worksheet
    :return: List( String )
    """
    return [
        "Fecha creación",
        "Año pago",
        "Mes pago",
        "Día pago",
        "Categoría",
        "Pagado por",
        "Monto"
    ]


def get_gasto_row_data(gasto):
    """
    Returns the data that will be written to the Gasto worksheet row.
    :param gasto: Gasto
    :return: List( String )
    """
    if not gasto.is_pending():
        data = [
            gasto.fecha_creacion,
            gasto.fecha_pago.year,
            gasto.fecha_pago.month,
            gasto.fecha_pago.day,
            gasto.categoria,
            gasto.usuario.user,
            gasto.monto
        ]
    else:
        data = [
            gasto.fecha_creacion,
            "-",
            "-",
            "-",
            gasto.categoria,
            "-",
            gasto.monto
        ]
    return data


def create_new_vivienda(form):
    new_viv = form.save()
    # add global categorias
    categorias_globales = Categoria.objects.filter(vivienda=None)
    for cat in categorias_globales:
        Categoria.objects.create(
            nombre=cat.nombre,
            vivienda=new_viv)
    # add initial Item instances
    new_viv.add_global_items()
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


def is_valid_transfer_to_user(user_id_raw, this_user):
    """
    Returns a tuple where:
    - if the user given by user_id_raw is a valid user for
    this_user to transfer to, the first element of the tuple
    is the User instance, and the second is an empty String.
    - if not, the first element is None and the second is an
    error message.
    """
    msg = ""
    try:
        user_id = int(user_id_raw)
    except (ValueError, TypeError):
        msg = "Debe especificar un usuario a quien transferirle."
        return (None, msg)

    user = ProxyUser.objects.filter(id=user_id).first()
    if user is None:
        msg = "Debe especificar un usuario a quien transferirle."
    elif user.get_vivienda()!=this_user.get_vivienda():
        msg = "El usuario indicado no pertenece a su Vivienda."
    elif user==this_user:
        msg = "¡No puede transferirse fondos a sí mismo!"

    if len(msg)>0:
        return (None, msg)
    return (user, "")


def is_valid_transfer_monto(monto_raw):
    """
    Returns a tuple where:
    - if the monto given by monto_raw is a valid monto, the
    first element of the tuple is the monto as an Integer,
    and the second is an empty String.
    - if not, the first element is None and the second is an
    error message.
    """
    try:
        monto = int(monto_raw)
        if monto<=0:
            msg = "Debe ingresar un monto mayor que 0."
            return (None, msg)
    except (ValueError, TypeError):
        msg = "Debe ingresar un monto mayor que 0."
        return (None, msg)
    return (monto, "")