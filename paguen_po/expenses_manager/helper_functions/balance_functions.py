# -*- coding: utf-8 -*-


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
