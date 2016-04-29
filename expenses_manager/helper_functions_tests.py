from django.core.urlresolvers import resolve
from expenses_manager.models import *


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
        vivienda_A,
        test_user_1_viv_A) = get_test_user_with_vivienda_and_login(
        test)
    # get roommate for rist user
    test_user_2 = ProxyUser.objects.create(
        username="test_user_2", email="b@b.com")
    test_user_2_viv_A = ViviendaUsuario.objects.create(
        vivienda=vivienda_A, user=test_user_2)
    # get another vivienda with another user
    test_user_3 = ProxyUser.objects.create(
        username="test_user_3", email="c@c.com")
    vivienda_B = Vivienda.objects.create(alias="vivB")
    test_user_3_viv_B = ViviendaUsuario.objects.create(
        vivienda=vivienda_B, user=test_user_3)
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
    test.assertContains(response, "Listas", status_code=status_code)


def has_not_logged_navbar(test, response, status_code=200):
    test.assertNotContains(response, "Salir", status_code=status_code)
    test.assertContains(response, "Entrar", status_code=status_code)
    test.assertContains(response, "Registrarse", status_code=status_code)


def has_logged_navbar(test, response, test_user, status_code=200):
    test.assertContains(response, "Salir", status_code=status_code)
    test.assertNotContains(response, "Entrar", status_code=status_code)
    test.assertNotContains(response, "Registrarse", status_code=status_code)
    test.assertContains(response, test_user.username, status_code=status_code)


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
    test.assertContains(response, user.username)
    test.assertContains(response, "Salir")
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
    test.assertContains(response, user.username)
    test.assertContains(response, "Salir")
    if user.has_vivienda():
        test.assertContains(response, "Gastos")
        test.assertContains(response, "Listas")
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
