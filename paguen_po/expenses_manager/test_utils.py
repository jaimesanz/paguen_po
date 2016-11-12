# -*- coding: utf-8 -*-
from django.core.urlresolvers import resolve
from django.utils import timezone

from .models import ViviendaUsuario, Gasto, \
    ListaCompras, Item, ItemLista
from categories.models import Categoria
from households.models import Vivienda, ViviendaUsuario
from users.models import ProxyUser


# functions for generating test databases
def get_lone_user():
    return ProxyUser.objects.create(username="us1", email="a@a.com")


def get_vivienda_with_1_user():
    user1 = get_lone_user()
    correct_vivienda = Vivienda.objects.create(alias="viv1")
    user1_viv = ViviendaUsuario.objects.create(
        vivienda=correct_vivienda, user=user1)
    return (user1, correct_vivienda, user1_viv)


def get_vivienda_with_2_users():
    user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
    user2 = ProxyUser.objects.create(username="us2", email="b@b.com")
    user2_viv = ViviendaUsuario.objects.create(
        vivienda=correct_vivienda, user=user2)
    return (user1, user2, correct_vivienda, user1_viv, user2_viv)


def get_dummy_gasto_pendiente(user_viv):
    dummy_categoria = Categoria.objects.create(nombre="dummy")
    gasto = Gasto.objects.create(
        monto=1000,
        creado_por=user_viv,
        categoria=dummy_categoria)
    return gasto, dummy_categoria


def get_dummy_lista_with_1_item(user_viv):
    lista = ListaCompras.objects.create(usuario_creacion=user_viv)
    item = Item.objects.create(nombre="test_item_1")
    user_viv.vivienda.add_global_items()
    item = Item.objects.get(nombre=item.nombre, vivienda=user_viv.vivienda)
    item_lista = ItemLista.objects.create(
        item=item,
        lista=lista,
        cantidad_solicitada=10)
    return (lista, item, item_lista)


def get_dummy_lista_with_2_items(user_viv):
    lista, item_1, item_lista_1 = get_dummy_lista_with_1_item(user_viv)
    item_2 = Item.objects.create(nombre="test_item_2")
    user_viv.vivienda.add_global_items()
    item_2 = Item.objects.get(nombre=item_2.nombre, vivienda=user_viv.vivienda)
    item_lista_2 = ItemLista.objects.create(
        item=item_2,
        lista=lista,
        cantidad_solicitada=20)
    return lista, item_1, item_lista_1, item_2, item_lista_2


def get_test_user():
    user = ProxyUser.objects.create(username="test_user_1", email="a@a.com")
    user.set_password("holahola")
    user.save()
    return user


def get_test_user_and_login(test):
    test_user = get_test_user()
    test.client.login(username=test_user.username, password="holahola")
    return test_user


def get_test_user_with_vivienda_and_login(test):
    test_user = get_test_user_and_login(test)
    vivienda = Vivienda.objects.create(alias="vivA")
    test_user_viv = ViviendaUsuario.objects.create(
        vivienda=vivienda, user=test_user)
    return test_user, vivienda, test_user_viv


def get_basic_setup_and_login_user_1(test):
    """
    Creates a Vivienda with 2 users (and logs in 1 of them),
    and another vivienda with 1 user.
    Returns the user that is logged in, his roommate and the third one
    """
    # get first user
    (test_user_1,
        vivienda_a,
        test_user_1_viv_a) = get_test_user_with_vivienda_and_login(
        test)
    # get roommate for rist user
    test_user_2 = ProxyUser.objects.create(
        username="test_user_2", email="b@b.com")
    test_user_2_viv_a = ViviendaUsuario.objects.create(
        vivienda=vivienda_a, user=test_user_2)
    # get another vivienda with another user
    test_user_3 = ProxyUser.objects.create(
        username="test_user_3", email="c@c.com")
    vivienda_b = Vivienda.objects.create(alias="vivB")
    test_user_3_viv_b= ViviendaUsuario.objects.create(
        vivienda=vivienda_b, user=test_user_3)
    return test_user_1, test_user_2, test_user_3


def get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(test):
    test_user_1, test_user_2, test_user_3 = get_basic_setup_and_login_user_1(
        test)

    dummy_categoria_global = Categoria.objects.create(nombre="dummy1")
    dummy_categoria_viv1 = Categoria.objects.create(
        nombre="dummy1",
        vivienda=test_user_1.get_vivienda())
    dummy_categoria_viv2 = Categoria.objects.create(
        nombre="dummy1",
        vivienda=test_user_3.get_vivienda())
    gasto_1 = Gasto.objects.create(
        monto=111,
        creado_por=test_user_1.get_vu(),
        categoria=dummy_categoria_viv1)
    gasto_2 = Gasto.objects.create(
        monto=222,
        creado_por=test_user_2.get_vu(),
        categoria=dummy_categoria_viv1)
    gasto_3 = Gasto.objects.create(
        monto=333,
        creado_por=test_user_3.get_vu(),
        categoria=dummy_categoria_viv2)

    test.assertEqual(Gasto.objects.filter(
        estado__estado="pendiente").count(), 3)
    test.assertEqual(Gasto.objects.filter(
        creado_por__vivienda=test_user_1.get_vivienda()).count(),
        2)
    test.assertEqual(Gasto.objects.filter(
        creado_por__vivienda=test_user_2.get_vivienda()).count(),
        2)
    test.assertEqual(Gasto.objects.filter(
        creado_por__vivienda=test_user_3.get_vivienda()).count(),
        1)

    return (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria_viv1,
            gasto_1,
            gasto_2,
            gasto_3)


def get_setup_with_gastos_items_and_listas(test):
    """
    The same as get_setup_viv_2_users_viv_1_user_cat_1_gastos_3, plus 3 dummy
    items and 2 dummy Listas:
    - one for the logged user's vivienda with items A and B
    - one for the other vivienda with item C
    Returns the user that's logged in
    """
    (test_user_1,
        test_user_2,
        test_user_3,
        dummy_categoria,
        gasto_1,
        gasto_2,
        gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
        test)
    # global items
    Item.objects.create(nombre="d1")
    Item.objects.create(nombre="d2")
    Item.objects.create(nombre="d3")

    test_user_1.get_vivienda().add_global_items()
    test_user_3.get_vivienda().add_global_items()

    item_1 = Item.objects.get(nombre="d1", vivienda=test_user_1.get_vivienda())
    item_2 = Item.objects.get(nombre="d2", vivienda=test_user_1.get_vivienda())
    item_3 = Item.objects.get(nombre="d3", vivienda=test_user_3.get_vivienda())

    lista_1 = ListaCompras.objects.create(
        usuario_creacion=test_user_1.get_vu())
    lista_2 = ListaCompras.objects.create(
        usuario_creacion=test_user_3.get_vu())

    il_1 = ItemLista.objects.create(
        item=item_1, lista=lista_1, cantidad_solicitada=1)
    il_2 = ItemLista.objects.create(
        item=item_2, lista=lista_1, cantidad_solicitada=2)

    il_3 = ItemLista.objects.create(
        item=item_3, lista=lista_2, cantidad_solicitada=3)

    return test_user_1


def get_setup_w_vivienda_3_users_and_periods():
    """
    Creates a Vivienda with 3 users, 1 default categoria, 1 categoria shared
    on leave and 5 dates
    """
    db = dict()
    # get Vivienda with 3 users
    (user1,
     user2,
     vivienda,
     user1_viv,
     user2_viv) = get_vivienda_with_2_users()
    user3 = ProxyUser.objects.create(username="us3", email="c@c.com")
    user3_viv = ViviendaUsuario.objects.create(
        vivienda=vivienda, user=user3)
    # create 2 categorias A, B
    cat_not_shared_on_leave = Categoria.objects.create(
        nombre="cat_1",
        vivienda=vivienda,
        is_shared=True,
        is_shared_on_leave=False)
    cat_shared_on_leave = Categoria.objects.create(
        nombre="cat_2",
        vivienda=vivienda,
        is_shared=True,
        is_shared_on_leave=True)

    db["user1"] = user1
    db["user2"] = user2
    db["vivienda"] = vivienda
    db["user1_viv"] = user1_viv
    db["user2_viv"] = user2_viv
    db["user3"] = user3
    db["user3_viv"] = user3_viv

    db["cat_not_shared_on_leave"] = cat_not_shared_on_leave
    db["cat_shared_on_leave"] = cat_shared_on_leave

    today = timezone.now().date()
    db["pA"] = today + timezone.timedelta(weeks=1)
    db["pB"] = today + timezone.timedelta(weeks=2)
    db["pC"] = today + timezone.timedelta(weeks=3)
    db["pD"] = today + timezone.timedelta(weeks=4)
    db["pE"] = today + timezone.timedelta(weeks=5)
    db["pF"] = today + timezone.timedelta(weeks=6)

    return db


def get_hard_balance_test_database():
    """
    Creates complex database case for balancing Gastos:
    - 3 users total
    - 1 user left
    - users had vacations
    - some gastos are shared on vacation, others are not
    """
    db = get_setup_w_vivienda_3_users_and_periods()

    user1 = db["user1"]
    user2 = db["user2"]
    user3 = db["user3"]
    user1_viv = db["user1_viv"]
    user2_viv = db["user2_viv"]
    user3_viv = db["user3_viv"]
    vivienda = db["vivienda"]

    user2_viv.fecha_creacion = db["pA"]
    user2_viv.fecha_abandono = db["pD"]
    user2_viv.estado = "inactivo"
    user3_viv.fecha_creacion = db["pC"]

    user1.go_on_vacation(start_date=db["pB"], end_date=db["pC"])
    user3.go_on_vacation(start_date=db["pD"], end_date=db["pE"])

    # u/p |a|b|c|d|e|f|...
    # --------------------
    # 1   |x|-|-|x|x|x|...
    # 2   |x|x|x|x|
    # 3       |x|-|-|x|...

    # create categorias
    cat_not_shared_on_leave = db["cat_not_shared_on_leave"]
    cat_shared_on_leave = db["cat_shared_on_leave"]

    def N(user, monto, p):
        gasto = Gasto.objects.create(
            monto=monto,
            creado_por=user,
            categoria=cat_not_shared_on_leave)
        user.confirm_pay(gasto, fecha_pago=p)

    def S(user, monto, p):
        gasto = Gasto.objects.create(
            monto=monto,
            creado_por=user,
            categoria=cat_shared_on_leave)
        user.confirm_pay(gasto, fecha_pago=p)

    # create gastos per period
    monto = 1000
    # a
    N(user1_viv, monto, db["pA"])  # 1 2
    N(user2_viv, monto, db["pA"])  # 1 2

    S(user2_viv, monto, db["pA"])  # 1 2
    # b
    N(user2_viv, monto, db["pB"])  # 2

    S(user2_viv, monto, db["pB"])  # 1 2
    S(user2_viv, monto, db["pB"])  # 1 2
    # c
    N(user2_viv, monto, db["pC"])  # 2 3
    N(user2_viv, monto, db["pC"])  # 2 3
    N(user3_viv, monto, db["pC"])  # 2 3

    S(user2_viv, monto, db["pC"])  # 1 2 3
    S(user3_viv, monto, db["pC"])  # 1 2 3
    S(user3_viv, monto, db["pC"])  # 1 2 3
    # d
    N(user1_viv, monto, db["pD"])  # 1 2
    N(user1_viv, monto, db["pD"])  # 1 2
    N(user2_viv, monto, db["pD"])  # 1 2

    S(user1_viv, monto, db["pD"])  # 1 2 3
    S(user1_viv, monto, db["pD"])  # 1 2 3
    S(user2_viv, monto, db["pD"])  # 1 2 3
    # e
    N(user1_viv, monto, db["pE"])  # 1

    S(user1_viv, monto, db["pE"])  # 1 3
    S(user1_viv, monto, db["pE"])  # 1 3
    # f
    N(user1_viv, monto, db["pF"])  # 1 3
    N(user1_viv, monto, db["pF"])  # 1 3
    N(user3_viv, monto, db["pF"])  # 1 3

    S(user1_viv, monto, db["pF"])  # 1 3
    S(user3_viv, monto, db["pF"])  # 1 3

    # save user2_viv so that it is mark as not active
    # thiis has to be done after creating the gastos because otherwise
    # the user can't pay Gastos! This is not a problem, it's just
    # inconvenient for creating tests...
    user2_viv.save()
    user3_viv.save()

    return db


def get_HARDEST_balance_test_database():
    """
    Creates complex database case for balancing Gastos:
    - 5 users total
    - users have left
    - users had vacations
    - users have vacations
    - some gastos are shared on vacation, others are not
    """
    # inb4: this test is highly read only xD
    # get vivienda with many users and create gastos
    db = get_setup_w_vivienda_3_users_and_periods()
    user1 = db["user1"]
    user2 = db["user2"]
    user3 = db["user3"]
    user1_viv = db["user1_viv"]
    user2_viv = db["user2_viv"]
    user3_viv = db["user3_viv"]
    vivienda = db["vivienda"]
    # create all necessary periods. Last period of dict is today -> "n"
    p = dict()
    today = timezone.now().date()
    step = 2  # in weeks
    delta = 0  # start today
    for period_label in "nmlkjihgfedcba":
        p[period_label] = today - timezone.timedelta(weeks=delta)
        delta += step

    # need 2 more users
    user4 = ProxyUser.objects.create(username="us4", email="d@d.com")
    user4_viv = ViviendaUsuario.objects.create(
        vivienda=vivienda, user=user4)
    user5 = ProxyUser.objects.create(username="us5", email="e@e.com")
    user5_viv = ViviendaUsuario.objects.create(
        vivienda=vivienda, user=user5)

    # define periods on which users were actually active
    # user1 still acitve
    user1_viv.fecha_creacion = p["a"]
    # user2 not active anymore
    user2_viv.fecha_creacion = p["a"]
    user2_viv.fecha_abandono = p["f"]
    user2_viv.estado = "inactivo"
    # user3 not active anymore
    user3_viv.fecha_creacion = p["c"]
    user3_viv.fecha_abandono = p["j"]
    user3_viv.estado = "inactivo"
    # user4 still acitve
    user4_viv.fecha_creacion = p["b"]
    # user5 still acitve
    user5_viv.fecha_creacion = p["k"]

    # this table shows the users vs periods
    # users join vivienda in "s", and leave it on "e"
    # users with an "e" in column infinity means they are still active,
    # ie, they haven't left yet
    # u/p |a|b|c|d|e|f|g|h|i|j|k|l|m|n| ... | infinity
    # ----------------------------------------
    # 1   |s| | | | | | | | | | | | | | ... | e
    # 2   |s| | | | |e| | | | | | | | | ... |
    # 3   | | |s| | | | | | |e| | | | | ... |
    # 4   | |s| | | | | | | | | | | | | ... | e
    # 5   | | | | | | | | | | |s| | | | ... | e

    # define periods on which users were on vacations
    # user1
    user1.go_on_vacation(start_date=p["e"], end_date=p["g"])
    user1.go_on_vacation(start_date=p["k"], end_date=p["m"])
    # user2
    user2.go_on_vacation(start_date=p["b"], end_date=p["d"])
    # user3
    user3.go_on_vacation(start_date=p["e"], end_date=p["g"])
    # user4
    user4.go_on_vacation(start_date=p["h"], end_date=p["i"])
    user4.go_on_vacation(start_date=p["l"], end_date=p["m"])
    # user5 has no vacations

    # save all these changes
    user1_viv.save()
    user2_viv.save()
    user3_viv.save()
    user4_viv.save()
    user5_viv.save()

    # now we add vacations to the table; an "A" means the user starts
    # a vacation, and a "Z" means the user came back from that vacation

    # u/p |a|b|c|d|e|f|g|h|i|j|k|l|m|n| ... | infinity
    # ----------------------------------------
    # 1   |s| | | |A| |Z| | | |A| |Z| | ... | e
    # 2   |s|A| |Z| |e| | | | | | | | | ... |
    # 3   | | |s| |A| |Z| | |e| | | | | ... |
    # 4   | |s| | | | | |A|Z| | |A|Z| | ... | e
    # 5   | | | | | | | | | | |s| | | | ... | e
    # --------------------------------------------------
    # u/p |a|b|c|d|e|f|g|h|i|j|k|l|m|n| ... | infinity

    # Now, an "x" means the user was active in that date, and
    # a "-" means he/she was on vacation. Removed periods where the user
    # was not active at all.

    # u/p |a|b|c|d|e|f|g|h|i|j|k|l|m|n| ... | infinity
    # ----------------------------------------
    # 1   |x|x|x|x|-|-|-|x|x|x|-|-|-|x| ... | e
    # 2   |x|-|-|-|x|x|
    # 3       |x|x|-|-|-|x|x|x|
    # 4     |x|x|x|x|x|x|-|-|x|x|-|-|x| ... | e
    # 5                       |x|x|x|x| ... | e
    # --------------------------------------------------
    # u/p |a|b|c|d|e|f|g|h|i|j|k|l|m|n| ... | infinity

    cat_not_shared_on_leave = db["cat_not_shared_on_leave"]
    cat_shared_on_leave = db["cat_shared_on_leave"]

    def N(user, monto, p):
        gasto = Gasto.objects.create(
            monto=monto,
            creado_por=user,
            categoria=cat_not_shared_on_leave)
        user.confirm_pay(gasto, fecha_pago=p)

    def S(user, monto, p):
        gasto = Gasto.objects.create(
            monto=monto,
            creado_por=user,
            categoria=cat_shared_on_leave)
        user.confirm_pay(gasto, fecha_pago=p)
    # create gastos per period
    # import random
    # dummy_monto = random.randint(10000, 50000)
    # print(dummy_monto)
    dummy_monto = 1000
    # a
    N(user1_viv, dummy_monto, p["a"])  # 1 2
    N(user1_viv, dummy_monto, p["a"])  # 1 2
    N(user2_viv, dummy_monto, p["a"])  # 1 2
    # b
    N(user1_viv, dummy_monto, p["b"])  # 1 4
    N(user4_viv, dummy_monto, p["b"])  # 1 4

    S(user1_viv, dummy_monto, p["b"])  # 1 2 4
    # c
    N(user1_viv, dummy_monto, p["c"])  # 1 3 4
    N(user2_viv, dummy_monto, p["c"])  # 1 3 4
    N(user2_viv, dummy_monto, p["c"])  # 1 3 4
    N(user3_viv, dummy_monto, p["c"])  # 1 3 4

    S(user1_viv, dummy_monto, p["c"])  # 1 2 3 4
    S(user3_viv, dummy_monto, p["c"])  # 1 2 3 4
    # d
    N(user1_viv, dummy_monto, p["d"])  # 1 3 4
    N(user1_viv, dummy_monto, p["d"])  # 1 3 4
    N(user3_viv, dummy_monto, p["d"])  # 1 3 4

    S(user2_viv, dummy_monto, p["d"])  # 1 2 3 4
    S(user2_viv, dummy_monto, p["d"])  # 1 2 3 4
    S(user3_viv, dummy_monto, p["d"])  # 1 2 3 4
    # e
    N(user2_viv, dummy_monto, p["e"])  # 2 4

    S(user2_viv, dummy_monto, p["e"])  # 1 2 3 4
    S(user4_viv, dummy_monto, p["e"])  # 1 2 3 4
    S(user4_viv, dummy_monto, p["e"])  # 1 2 3 4
    # f
    # g
    N(user4_viv, dummy_monto, p["g"])  # 4
    N(user4_viv, dummy_monto, p["g"])  # 4
    N(user4_viv, dummy_monto, p["g"])  # 4

    S(user4_viv, dummy_monto, p["g"])  # 1 3 4
    # h
    N(user1_viv, dummy_monto, p["h"])  # 1 3

    S(user1_viv, dummy_monto, p["h"])  # 1 3 4
    S(user3_viv, dummy_monto, p["h"])  # 1 3 4
    S(user3_viv, dummy_monto, p["h"])  # 1 3 4
    # i
    # j
    N(user1_viv, dummy_monto, p["j"])  # 1 3 4
    N(user4_viv, dummy_monto, p["j"])  # 1 3 4
    N(user4_viv, dummy_monto, p["j"])  # 1 3 4

    S(user1_viv, dummy_monto, p["j"])  # 1 3 4
    S(user3_viv, dummy_monto, p["j"])  # 1 3 4
    S(user3_viv, dummy_monto, p["j"])  # 1 3 4
    # k
    N(user5_viv, dummy_monto, p["k"])  # 4 5

    S(user4_viv, dummy_monto, p["k"])  # 1 4 5
    S(user4_viv, dummy_monto, p["k"])  # 1 4 5
    S(user5_viv, dummy_monto, p["k"])  # 1 4 5
    # l
    N(user5_viv, dummy_monto, p["l"])  # 5
    N(user5_viv, dummy_monto, p["l"])  # 5
    N(user5_viv, dummy_monto, p["l"])  # 5

    S(user5_viv, dummy_monto, p["l"])  # 1 4 5
    # m
    N(user5_viv, dummy_monto, p["m"])  # 5

    S(user5_viv, dummy_monto, p["m"])  # 1 4 5
    S(user5_viv, dummy_monto, p["m"])  # 1 4 5
    S(user5_viv, dummy_monto, p["m"])  # 1 4 5
    # n
    N(user1_viv, dummy_monto, p["n"])  # 1 4 5
    N(user4_viv, dummy_monto, p["n"])  # 1 4 5

    S(user1_viv, dummy_monto, p["n"])  # 1 4 5
    S(user4_viv, dummy_monto, p["n"])  # 1 4 5
    S(user5_viv, dummy_monto, p["n"])  # 1 4 5
    S(user5_viv, dummy_monto, p["n"])  # 1 4 5

    return {
        "user1": user1,
        "user2": user2,
        "user3": user3,
        "user4": user4,
        "user5": user5,
        "user1_viv": user1_viv,
        "user2_viv": user2_viv,
        "user3_viv": user3_viv,
        "user4_viv": user4_viv,
        "user5_viv": user5_viv,
        "vivienda": vivienda,
        "pA": p["a"],
        "pB": p["b"],
        "pC": p["c"],
        "pD": p["d"],
        "pE": p["e"],
        "pF": p["f"]
    }


# common tests used in lots of views

def has_navbar_without_vivienda(test, response, status_code=200):
    test.assertContains(response, "Crear Vivienda")
    test.assertContains(response, "Invitaciones")
    test.assertNotContains(response, "Gastos")
    test.assertNotContains(response, "Listas")


def has_navbar_with_vivienda(test, response, status_code=200):
    test.assertNotContains(response,
                           "Crear Vivienda",
                           status_code=status_code)
    test.assertNotContains(
        response,
        "<li><a href=\"/invites_list\">Invitaciones</a></li>",
        status_code=status_code)
    test.assertContains(response, "Gastos", status_code=status_code)
    test.assertContains(response, "Lista", status_code=status_code)


def has_not_logged_navbar(test, response, status_code=200):
    test.assertContains(response, "Entrar", status_code=status_code)
    test.assertContains(response, "Registrarse", status_code=status_code)


def has_logged_navbar(test, response, test_user, status_code=200):
    test.assertNotContains(response, "Entrar", status_code=status_code)
    test.assertNotContains(response, "Registrarse", status_code=status_code)


def has_logged_navbar_without_viv(test, response, test_user, status_code=200):
    # is logged
    has_logged_navbar(test, response, test_user, status_code)
    # has no vivienda
    has_navbar_without_vivienda(test, response, status_code)


def has_logged_navbar_with_viv(test, response, test_user, status_code=200):
    # is logged
    has_logged_navbar(test, response, test_user, status_code)
    # has no vivienda
    has_navbar_with_vivienda(test, response, status_code)


def test_the_basics(test, url, template_name, view_func):
    """
    Tests: template loaded, corect html, resolves to correct view function
    """
    found = resolve(url)
    response = test.client.get(url, follow=True)

    test.assertTemplateUsed(response, template_name=template_name)
    test.assertEqual(found.func, view_func)

    return response


def test_the_basics_not_logged_in(test, url, template_name, view_func):
    """
    Tests the basics and checks navbar is logged out
    """
    response = test_the_basics(test, url, template_name, view_func)
    has_not_logged_navbar(test, response)


def execute_test_the_basics_logged_in(test, url, template_name, view_func):
    user = get_test_user_and_login(test)
    response = test_the_basics(test, url, template_name, view_func)
    test.assertNotContains(response, "Entrar")
    test.assertNotContains(response, "Registrarse")
    test.assertNotContains(response, "Inicio")
    if user.has_vivienda():
        test.assertContains(response, "Gastos")
        test.assertContains(response, "Listas")
        test.assertContains(response, "Vivienda")
    else:
        test.assertContains(response, "Crear")
        test.assertContains(response, "Invitaciones")


def execute_test_basics_logged_with_viv(test, url, template_name, view_func):
    user, vivienda, user_viv = get_test_user_with_vivienda_and_login(test)
    response = test_the_basics(test, url, template_name, view_func)
    test.assertNotContains(response, "Entrar")
    test.assertNotContains(response, "Registrarse")
    test.assertNotContains(response, "Inicio")
    if user.has_vivienda():
        test.assertContains(response, "Gastos")
        test.assertContains(response, "Lista")
        test.assertContains(response, "Vivienda")
    else:
        test.assertContains(response, "Crear")
        test.assertContains(response, "Invitaciones")


def execute_test_the_basics_not_logged_in_restricted(test, url):
    """
    Checks that the user was redirected to login page
    """
    response = test.client.get(url)

    test.assertRedirects(response, "/accounts/login/?next=" + url)
