from django.test import TestCase
from expenses_manager.models import *


##########################
# Helper functions
##########################


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


##########################
# Tests
##########################

class ProxyUserModelTest(TestCase):

    def test_user_ha_no_vivienda(self):
        user1 = get_lone_user()

        # user has no vivienda
        self.assertFalse(user1.has_vivienda())
        self.assertEqual(user1.get_vivienda(), None)
        self.assertEqual(user1.get_vu(), None)
        self.assertEqual(user1.get_roommates().count(), 0)

    def test_user_joins_vivienda(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()

        self.assertTrue(user1.has_vivienda())
        self.assertEqual(user1.get_vivienda().alias, "viv1")
        self.assertNotEqual(user1.get_vivienda().alias, "viv2")
        self.assertTrue(user1.get_roommates().count(), 1)
        self.assertIn(user1.get_vu(), user1.get_roommates())
        self.assertEqual(user1.get_vu(), user1_viv)

    def test_another_user_joins_vivienda(self):
        (user1,
         user2,
         correct_vivienda,
         user1_viv, user2_viv) = get_vivienda_with_2_users()

        self.assertEqual(user2.get_vivienda().alias, "viv1")
        self.assertNotEqual(user2.get_vivienda().alias, "viv2")
        self.assertEqual(user2.get_roommates().count(), 2)
        self.assertEqual(user1.get_roommates().count(),
                         user2.get_roommates().count())
        self.assertIn(user2.get_vu(), user2.get_roommates())
        self.assertIn(user1.get_vu(), user2.get_roommates())
        self.assertIn(user2.get_vu(), user1.get_roommates())
        self.assertIn(user1.get_vu(), user1.get_roommates())

    def test_user_leaves_vivienda_and_leaves_roommate_alone(self):
        (user1,
         user2,
         correct_vivienda,
         user1_viv,
         user2_viv) = get_vivienda_with_2_users()

        # first user leaves
        user1_viv.estado = "inactivo"
        user1_viv.save()
        # user1 is now vivienda-less
        self.assertFalse(user1.has_vivienda())
        self.assertEqual(user1.get_vivienda(), None)
        self.assertEqual(user1.get_vu(), None)
        self.assertEqual(user1.get_roommates().count(), 0)
        # user2 is still in the vivienda, but is now alone
        self.assertEqual(user2.get_vivienda().alias, "viv1")
        self.assertNotEqual(user2.get_vivienda().alias, "viv2")
        self.assertTrue(user2.get_roommates().count(), 1)
        self.assertIn(user2.get_vu(), user2.get_roommates())
        self.assertNotIn(user1.get_vu(), user2.get_roommates())
        self.assertNotEqual(user1.get_roommates().count(),
                            user2.get_roommates().count())

    def test_user_leaves_vivienda_and_joins_a_new_one(self):
        (user1,
         user2,
         correct_vivienda,
         user1_viv,
         user2_viv) = get_vivienda_with_2_users()
        other_vivienda = Vivienda.objects.create(alias="viv2")

        # first user leaves and joins another
        user1_viv.estado = "inactivo"
        user1_viv.save()
        user1_new_viv = ViviendaUsuario.objects.create(
            vivienda=other_vivienda, user=user1)

        # user1 is now in a vivienda, but alone
        self.assertEqual(user1.get_vivienda().alias, "viv2")
        self.assertNotEqual(user1.get_vivienda().alias, "viv1")
        self.assertTrue(len(user1.get_roommates()), 1)
        # user2 is still in the first vivienda, but is now alone
        self.assertEqual(user2.get_vivienda().alias, "viv1")
        self.assertNotEqual(user2.get_vivienda().alias, "viv2")
        self.assertTrue(len(user2.get_roommates()), 1)

    def test_lone_user_has_no_invites(self):
        user1 = get_lone_user()

        # user has no invites
        invites_in, invites_out = user1.get_invites()
        self.assertEqual(invites_in.count(), 0)
        self.assertEqual(invites_out.count(), 0)

    def test_user_invites_another(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        user2 = ProxyUser.objects.create(username="us2", email="b@b.com")

        invite = Invitacion.objects.create(
            invitado=user2, invitado_por=user1_viv, email="b@b.com")
        self.assertEqual(user2.get_invites()[0].count(), 1)
        self.assertEqual(user1.get_invites()[1].count(), 1)
        self.assertTrue(user1.sent_invite(invite))
        self.assertTrue(user1_viv.sent_invite(invite))
        self.assertFalse(user2.sent_invite(invite))

    def test_user_accepts_invite(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        user2 = ProxyUser.objects.create(username="us2", email="b@b.com")

        invite = Invitacion.objects.create(
            invitado=user2, invitado_por=user1_viv, email="b@b.com")
        invite.accept()

        self.assertEqual(user2.get_invites()[0].count(), 0)
        self.assertEqual(user1.get_invites()[1].count(), 0)

        # user2 joined the vivienda
        self.assertEqual(user2.get_vivienda().alias, "viv1")
        self.assertNotEqual(user2.get_vivienda().alias, "viv2")
        self.assertEqual(user2.get_roommates().count(), 2)
        self.assertEqual(user1.get_roommates().count(),
                         user2.get_roommates().count())
        self.assertIn(user2.get_vu(), user2.get_roommates())
        self.assertIn(user1.get_vu(), user2.get_roommates())
        self.assertIn(user2.get_vu(), user1.get_roommates())
        self.assertIn(user1.get_vu(), user1.get_roommates())

    def test_user_rejects_invite(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        user2 = ProxyUser.objects.create(username="us2", email="b@b.com")

        invite = Invitacion.objects.create(
            invitado=user2, invitado_por=user1_viv, email="b@b.com")
        invite.reject()

        self.assertEqual(user2.get_invites()[0].count(), 0)
        self.assertEqual(user1.get_invites()[1].count(), 0)

        # user2 didn't join the vivienda
        self.assertFalse(user2.has_vivienda())
        self.assertEqual(user2.get_vivienda(), None)
        self.assertEqual(user2.get_vu(), None)
        self.assertEqual(user2.get_roommates().count(), 0)
        # user1 is still in the vivienda
        self.assertTrue(user1.has_vivienda())
        self.assertEqual(user1.get_vivienda().alias, "viv1")
        self.assertTrue(user1.get_roommates().count(), 1)
        self.assertIn(user1.get_vu(), user1.get_roommates())
        self.assertEqual(user1.get_vu(), user1_viv)

    def test_user_leaves_and_returns(self):
        (user1,
         user2,
         correct_vivienda,
         user1_viv,
         user2_viv) = get_vivienda_with_2_users()

        # first user leaves and returns
        user1_viv.estado = "inactivo"
        user1_viv.save()
        ViviendaUsuario.objects.create(vivienda=correct_vivienda, user=user1)

        # both users are in the vivienda
        self.assertEqual(user2.get_vivienda().alias, "viv1")
        self.assertEqual(user2.get_roommates().count(), 2)
        self.assertEqual(user1.get_roommates().count(),
                         user2.get_roommates().count())
        self.assertIn(user2.get_vu(), user2.get_roommates())
        self.assertIn(user1.get_vu(), user2.get_roommates())
        self.assertIn(user2.get_vu(), user1.get_roommates())
        self.assertIn(user1.get_vu(), user1.get_roommates())

    def test_user_pays_gasto(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        gasto, dummy_categoria = get_dummy_gasto_pendiente(user1_viv)

        self.assertFalse(gasto.is_paid())
        self.assertTrue(gasto.is_pending())
        self.assertTrue(gasto.allow_user(user1))
        user1.pagar(gasto)
        self.assertFalse(gasto.is_pending())
        self.assertTrue(gasto.is_paid())
        self.assertTrue(gasto.allow_user(user1))


class ViviendaModelTest(TestCase):

    def test_get_gastos_from_vivienda_without_gastos(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()

        gastos_pendientes_direct = correct_vivienda.get_gastos_pendientes()
        gastos_pagados_direct = correct_vivienda.get_gastos_pagados()
        gastos_pendientes, gastos_pagados = correct_vivienda.get_gastos()

        self.assertEqual(gastos_pendientes.count(), 0)
        self.assertEqual(gastos_pagados.count(), 0)
        self.assertEqual(gastos_pendientes_direct.count(), 0)
        self.assertEqual(gastos_pagados_direct.count(), 0)

    def test_get_gastos_from_vivienda_with_gastos_pendientes(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        gasto, dummy_categoria = get_dummy_gasto_pendiente(user1_viv)

        gastos_pendientes_direct = correct_vivienda.get_gastos_pendientes()
        gastos_pagados_direct = correct_vivienda.get_gastos_pagados()
        gastos_pendientes, gastos_pagados = correct_vivienda.get_gastos()

        self.assertEqual(gastos_pendientes.count(), 1)
        self.assertEqual(gastos_pagados.count(), 0)
        self.assertEqual(gastos_pendientes_direct.count(), 1)
        self.assertEqual(gastos_pagados_direct.count(), 0)

    def test_get_gastos_from_vivienda_with_gastos_pagados(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        gasto, dummy_categoria = get_dummy_gasto_pendiente(user1_viv)
        user1.pagar(gasto)

        gastos_pendientes_direct = correct_vivienda.get_gastos_pendientes()
        gastos_pagados_direct = correct_vivienda.get_gastos_pagados()
        gastos_pendientes, gastos_pagados = correct_vivienda.get_gastos()

        self.assertEqual(gastos_pendientes.count(), 0)
        self.assertEqual(gastos_pagados.count(), 1)
        self.assertEqual(gastos_pendientes_direct.count(), 0)
        self.assertEqual(gastos_pagados_direct.count(), 1)

    def test_add_new_categoria(self):
        user, vivienda, user_viv = get_vivienda_with_1_user()
        dummy_categoria = Categoria.objects.create(nombre="dummy1")

        vivienda.add_categoria("dummy2")

        self.assertEqual(
            Categoria.objects.count(),
            2)
        viv_cat = Categoria.objects.filter(vivienda=vivienda).first()
        self.assertFalse(viv_cat.hidden)
        self.assertFalse(viv_cat.is_global())


class ViviendaUsuarioModelTest(TestCase):

    def test_user_leaves_vivienda(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        self.assertTrue(user1_viv.is_active())
        self.assertEqual(user1_viv.fecha_abandono, None)

        user1_viv.leave()

        self.assertFalse(user1.has_vivienda())
        self.assertFalse(user1_viv.is_active())
        self.assertNotEqual(ViviendaUsuario.objects.get(
            id=user1_viv.id).fecha_abandono, None)

    def test_user_gets_gastos_of_vivienda_that_has_no_gastos(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()

        gastos_pendientes, gastos_pagados = user1_viv.get_gastos_vivienda()

        self.assertEqual(gastos_pendientes.count(), 0)
        self.assertEqual(gastos_pagados.count(), 0)

    def test_user_gets_gastos_of_vivienda_that_has_gastos_pendientes(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        gasto, dummy_categoria = get_dummy_gasto_pendiente(user1_viv)

        gastos_pendientes, gastos_pagados = user1_viv.get_gastos_vivienda()

        self.assertEqual(gastos_pendientes.count(), 1)
        self.assertEqual(gastos_pagados.count(), 0)

    def test_user_gets_gastos_of_vivienda_that_has_gastos_pagados(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        gasto, dummy_categoria = get_dummy_gasto_pendiente(user1_viv)
        user1.pagar(gasto)

        gastos_pendientes, gastos_pagados = user1_viv.get_gastos_vivienda()

        self.assertEqual(gastos_pendientes.count(), 0)
        self.assertEqual(gastos_pagados.count(), 1)

    def test_user_gets_gastos_of_viv_that_has_gastos_pend_and_pays_them(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        gasto, dummy_categoria = get_dummy_gasto_pendiente(user1_viv)
        user1_viv.pagar(gasto)

        gastos_pendientes, gastos_pagados = user1_viv.get_gastos_vivienda()

        self.assertEqual(gastos_pendientes.count(), 0)
        self.assertEqual(gastos_pagados.count(), 1)

    def test_user_invites_another(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        user2 = ProxyUser.objects.create(username="us2", email="b@b.com")
        invite = Invitacion.objects.create(
            invitado=user2, invitado_por=user1_viv, email="b@b.com")

        self.assertTrue(user1_viv.sent_invite(invite))


class InvitacionModelTest(TestCase):
    # TODO test this methods:
    # is_invited_user
    # is_invited_by_user

    def test_new_invite_has_pending_state(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        user2 = ProxyUser.objects.create(username="us2", email="b@b.com")
        invite = Invitacion.objects.create(
            invitado=user2, invitado_por=user1_viv, email="b@b.com")

        self.assertEqual(invite.estado, "pendiente")

    def test_accept(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        user2 = ProxyUser.objects.create(username="us2", email="b@b.com")
        invite = Invitacion.objects.create(
            invitado=user2, invitado_por=user1_viv, email="b@b.com")

        invite.accept()

        self.assertEqual(invite.estado, "aceptada")

    def test_reject(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        user2 = ProxyUser.objects.create(username="us2", email="b@b.com")
        invite = Invitacion.objects.create(
            invitado=user2, invitado_por=user1_viv, email="b@b.com")

        invite.reject()

        self.assertEqual(invite.estado, "rechazada")

    def test_cancel(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        user2 = ProxyUser.objects.create(username="us2", email="b@b.com")
        invite = Invitacion.objects.create(
            invitado=user2, invitado_por=user1_viv, email="b@b.com")

        invite.reject()

        self.assertEqual(invite.estado, "rechazada")

    def test_is_invited_user(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        user2 = ProxyUser.objects.create(username="us2", email="b@b.com")
        invite = Invitacion.objects.create(
            invitado=user2, invitado_por=user1_viv, email="b@b.com")

        self.assertTrue(invite.is_invited_user(user2))
        self.assertFalse(invite.is_invited_user(user1))

    def test_is_invited_by_user(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        user2 = ProxyUser.objects.create(username="us2", email="b@b.com")
        invite = Invitacion.objects.create(
            invitado=user2, invitado_por=user1_viv, email="b@b.com")

        self.assertTrue(invite.is_invited_by_user(user1))
        self.assertFalse(invite.is_invited_by_user(user2))
        self.assertTrue(invite.is_invited_by_user(user1_viv))


class SolicitudAbandonarViviendaModelTest(TestCase):
    pass


class CategoriaModelTest(TestCase):
    pass


class ItemModelTest(TestCase):

    def test_is_in_lista(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        lista, item, item_lista = get_dummy_lista_with_1_item(user1_viv)

        self.assertTrue(item.is_in_lista(lista))

    def test_is_not_in_lista(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        lista, item_1, item_lista_1 = get_dummy_lista_with_1_item(user1_viv)
        item_2 = Item.objects.create(
            nombre="test_item_2",
            vivienda=correct_vivienda)

        self.assertFalse(item_2.is_in_lista(lista))

    def test_is_in_None_lista(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        lista, item_1, item_lista_1 = get_dummy_lista_with_1_item(user1_viv)

        self.assertFalse(item_1.is_in_lista(None))


class YearMonthModelTest(TestCase):

    def test_year_month_gets_correct_next_period_easy(self):
        this_period, __ = YearMonth.objects.get_or_create(year=2016, month=4)
        next_year, next_month = this_period.get_next_period()

        self.assertEqual(next_year, 2016)
        self.assertEqual(next_month, 5)

    def test_year_month_gets_correct_next_period_december(self):
        this_period, __ = YearMonth.objects.get_or_create(year=2016, month=12)
        next_year, next_month = this_period.get_next_period()

        self.assertEqual(next_year, 2017)
        self.assertEqual(next_month, 1)

    def test_year_month_gets_correct_next_period_november(self):
        this_period, __ = YearMonth.objects.get_or_create(year=2016, month=11)
        next_year, next_month = this_period.get_next_period()

        self.assertEqual(next_year, 2016)
        self.assertEqual(next_month, 12)

    def test_year_month_gets_correct_prev_period_easy(self):
        this_period, __ = YearMonth.objects.get_or_create(year=2016, month=4)
        prev_year, prev_month = this_period.get_prev_period()

        self.assertEqual(prev_year, 2016)
        self.assertEqual(prev_month, 3)

    def test_year_month_gets_correct_prev_period_january(self):
        this_period, __ = YearMonth.objects.get_or_create(year=2016, month=1)
        prev_year, prev_month = this_period.get_prev_period()

        self.assertEqual(prev_year, 2015)
        self.assertEqual(prev_month, 12)


class PresupuestoModelTest(TestCase):

    def test_get_total_expenses_returns_0_if_there_are_no_Gastos(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        presupuesto = Presupuesto.objects.create(
            categoria=Categoria.objects.create(
                nombre="dummy",
                vivienda=correct_vivienda),
            vivienda=correct_vivienda,
            monto=10000)

        self.assertEqual(presupuesto.get_total_expenses(), 0)

    def test_get_total_expenses_returns_0_if_there_are_no_paid_Gastos(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        dummy_categoria = Categoria.objects.create(
            nombre="dummy",
            vivienda=correct_vivienda)
        presupuesto = Presupuesto.objects.create(
            categoria=dummy_categoria,
            vivienda=correct_vivienda,
            monto=10000)
        gasto_1 = Gasto.objects.create(
            monto=1000,
            creado_por=user1_viv,
            categoria=dummy_categoria)
        gasto_2 = Gasto.objects.create(
            monto=2000,
            creado_por=user1_viv,
            categoria=dummy_categoria)

        self.assertTrue(gasto_1.is_pending())
        self.assertTrue(gasto_2.is_pending())
        self.assertEqual(presupuesto.get_total_expenses(), 0)

    def test_get_total_expenses_works_with_mix_of_pending_and_paid(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        dummy_categoria = Categoria.objects.create(
            nombre="dummy",
            vivienda=correct_vivienda)
        presupuesto = Presupuesto.objects.create(
            categoria=dummy_categoria,
            vivienda=correct_vivienda,
            monto=10000)
        gasto_1 = Gasto.objects.create(
            monto=1000,
            creado_por=user1_viv,
            categoria=dummy_categoria)
        gasto_2 = Gasto.objects.create(
            monto=2000,
            creado_por=user1_viv,
            categoria=dummy_categoria)
        gasto_2.pagar(user1)

        self.assertTrue(gasto_1.is_pending())
        self.assertFalse(gasto_2.is_pending())
        self.assertEqual(presupuesto.get_total_expenses(), 2000)

    def test_get_total_expenses_works_with_mix_of_categorias(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        dummy_categoria_1 = Categoria.objects.create(
            nombre="dummy1",
            vivienda=correct_vivienda)
        dummy_categoria_2 = Categoria.objects.create(
            nombre="dummy2",
            vivienda=correct_vivienda)
        presupuesto = Presupuesto.objects.create(
            categoria=dummy_categoria_1,
            vivienda=correct_vivienda,
            monto=10000)
        gasto_1 = Gasto.objects.create(
            monto=1000,
            creado_por=user1_viv,
            categoria=dummy_categoria_1)
        gasto_2 = Gasto.objects.create(
            monto=2000,
            creado_por=user1_viv,
            categoria=dummy_categoria_1)
        gasto_3 = Gasto.objects.create(
            monto=9000,
            creado_por=user1_viv,
            categoria=dummy_categoria_2)
        gasto_1.pagar(user1)
        gasto_2.pagar(user1)

        self.assertFalse(gasto_1.is_pending())
        self.assertFalse(gasto_2.is_pending())
        self.assertTrue(gasto_3.is_pending())
        self.assertEqual(presupuesto.get_total_expenses(), 3000)


class ListaComprasModelTest(TestCase):

    def test_default_values(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
         item_1,
         item_lista_1,
         item_2,
         item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        self.assertEqual(lista.estado, "pendiente")
        self.assertEqual(lista.usuario_creacion, user1_viv)

    def test_get_existing_item_by_name(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
         item_1,
         item_lista_1,
         item_2,
         item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        self.assertEqual(lista.get_item_by_name(
            item_1.nombre).nombre, item_1.nombre)
        self.assertEqual(lista.get_item_by_name(
            item_2.nombre).nombre, item_2.nombre)
        self.assertNotEqual(lista.get_item_by_name(
            item_1.nombre).nombre, item_2.nombre)
        self.assertNotEqual(lista.get_item_by_name(
            item_2.nombre).nombre, item_1.nombre)

    def test_get_non_existing_item_by_name(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
         item_1,
         item_lista_1,
         item_2,
         item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        self.assertEqual(lista.get_item_by_name("test_item_3"), None)

    def test_count_items_with_only_pending(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
         item_1,
         item_lista_1,
         item_2,
         item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        self.assertEqual(lista.count_items(), 2)

    def test_count_items_with_pending_and_paid(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
         item_1,
         item_lista_1,
         item_2,
         item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        item_lista_1.buy(1)
        self.assertEqual(lista.count_items(), 2)
        item_lista_2.buy(1)
        self.assertEqual(lista.count_items(), 2)

    def test_add_new_item(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
         item_1,
         item_lista_1,
         item_2,
         item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)
        new_item = Item.objects.create(
            nombre="test_item_3",
            vivienda=correct_vivienda)

        new_item_lista = lista.add_item(new_item, 30)

        self.assertEqual(lista.count_items(), 3)
        self.assertTrue(new_item_lista.is_pending())

    def test_add_existing_item(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
         item_1,
         item_lista_1,
         item_2,
         item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        new_item_lista = lista.add_item(item_1, 30)

        self.assertTrue(item_lista_1.is_pending())
        self.assertEqual(item_lista_1.cantidad_solicitada, 10)
        self.assertNotEqual(item_lista_1.cantidad_solicitada, 30)
        self.assertEqual(lista.count_items(), 2)
        self.assertEqual(new_item_lista, None)

    def test_add_new_item_by_name(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
         item_1,
         item_lista_1,
         item_2,
         item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)
        new_item = Item.objects.create(
            nombre="test_item_3",
            vivienda=correct_vivienda)

        new_item_lista = lista.add_item_by_name(new_item.nombre, 30)

        self.assertEqual(lista.count_items(), 3)
        self.assertTrue(new_item_lista.is_pending())

    def test_add_existing_item_by_name(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
         item_1,
         item_lista_1,
         item_2,
         item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        new_item_lista = lista.add_item_by_name(item_1.nombre, 30)

        self.assertTrue(item_lista_1.is_pending())
        self.assertEqual(item_lista_1.cantidad_solicitada, 10)
        self.assertNotEqual(item_lista_1.cantidad_solicitada, 30)
        self.assertEqual(lista.count_items(), 2)
        self.assertEqual(new_item_lista, None)

    def test_get_items_gets_nothing_on_new_list(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        lista = ListaCompras.objects.create(usuario_creacion=user1_viv)

        self.assertEqual(lista.get_items().count(), 0)

    def test_get_items_gets_all_items(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
         item_1,
         item_lista_1,
         item_2,
         item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        self.assertEqual(lista.get_items().count(), 2)
        item_lista_1.buy(1)
        self.assertEqual(lista.get_items().count(), 2)
        item_lista_2.buy(1)
        self.assertEqual(lista.get_items().count(), 2)

    def test_allow_user_is_true_for_creating_user(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
         item_1,
         item_lista_1,
         item_2,
         item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        self.assertTrue(lista.allow_user(user1))

    def test_allow_user_is_true_for_a_roommate(self):
        (user1,
         user2,
         correct_vivienda,
         user1_viv,
         user2_viv) = get_vivienda_with_2_users()
        (lista,
         item_1,
         item_lista_1,
         item_2,
         item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        self.assertTrue(lista.allow_user(user2))

    def test_allow_user_is_false_for_a_random_user(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
         item_1,
         item_lista_1,
         item_2,
         item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)
        user3 = ProxyUser.objects.create(username="us3", email="c@c.com")

        self.assertFalse(lista.allow_user(user3))

    def test_is_done_is_false_for_new_list(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
         item_1,
         item_lista_1,
         item_2,
         item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        self.assertFalse(lista.is_done())

    def test_is_done_is_false_for_new_list(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
         item_1,
         item_lista_1,
         item_2,
         item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)
        lista.estado = "pagada"
        lista.save()

        self.assertTrue(lista.is_done())

    def test_set_done_state_changes_the_state_to_done_and_returns_true(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
         item_1,
         item_lista_1,
         item_2,
         item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)
        ret = lista.set_done_state()

        self.assertTrue(lista.is_done())
        self.assertTrue(ret)

    def test_set_done_state_returns_false_if_state_was_already_done(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
         item_1,
         item_lista_1,
         item_2,
         item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)
        ret1 = lista.set_done_state()
        ret2 = lista.set_done_state()

        self.assertTrue(lista.is_done())
        self.assertFalse(ret2)

    def test_buy_item_changes_state_of_item(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
         item_1,
         item_lista_1,
         item_2,
         item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        lista.buy_item(item_lista_1.id, 10)

        self.assertEqual(ItemLista.objects.get(
            lista=lista, item=item_1).get_state(), "comprado")
        self.assertTrue(item_lista_2.is_pending())

    def test_buy_item_doesnt_change_number_of_items_in_lista(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
         item_1,
         item_lista_1,
         item_2,
         item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        lista.buy_item(item_lista_1.id, 10)
        self.assertEqual(lista.count_items(), 2)
        lista.buy_item(item_lista_2.id, 10)
        self.assertEqual(lista.count_items(), 2)

    def test_buy_list_changes_state_of_items_in_item_list(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
         item_1,
         item_lista_1,
         item_2,
         item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        lista.buy_list([(item_lista_1.id, 10)], 1000, user1_viv)

        self.assertTrue(lista.is_done())
        self.assertFalse(ItemLista.objects.get(
            lista=lista, item=item_1).is_pending())
        self.assertTrue(ItemLista.objects.get(
            lista=lista, item=item_2).is_pending())

    def test_buy_list_doesnt_change_anything_if_item_list_is_empty_array(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
            item_1,
            item_lista_1,
            item_2,
            item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        lista.buy_list([], 1000, user1_viv)

        self.assertFalse(lista.is_done())
        self.assertTrue(ItemLista.objects.get(
            lista=lista, item=item_1).is_pending())
        self.assertTrue(ItemLista.objects.get(
            lista=lista, item=item_2).is_pending())

    def test_buy_list_doesnt_change_anything_if_item_list_is_None(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
            item_1,
            item_lista_1,
            item_2,
            item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        lista.buy_list(None, 1000, user1_viv)

        self.assertFalse(lista.is_done())
        self.assertTrue(ItemLista.objects.get(
            lista=lista, item=item_1).is_pending())
        self.assertTrue(ItemLista.objects.get(
            lista=lista, item=item_2).is_pending())

    def test_get_gasto_returns_None_if_the_state_is_not_done(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
            item_1,
            item_lista_1,
            item_2,
            item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        self.assertFalse(lista.is_done())
        self.assertEqual(lista.get_gasto(), None)

    def test_get_gasto_returns_only_1_gasto_if_the_state_is_done(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
            item_1,
            item_lista_1,
            item_2,
            item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        gasto = lista.buy_list(
            [(item_lista_1.id, 10), (item_lista_2.id, 20)], 1000, user1_viv)

        self.assertTrue(lista.is_done())
        self.assertEqual(gasto, lista.get_gasto())
        self.assertEqual(gasto.monto, lista.get_gasto().monto)

    def test_get_missing_items_returns_all_items_for_a_new_list(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        lista = ListaCompras.objects.create(usuario_creacion=user1_viv)

        self.assertEqual(lista.get_missing_items().count(),
                         lista.get_items().count())

    def test_get_missing_items_return_1_item_in_list_w_1_paid_and_1_pend(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
            item_1,
            item_lista_1,
            item_2,
            item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        lista.buy_item(item_lista_1.id, 10)

        self.assertEqual(lista.get_missing_items().count(), 1)

    def test_has_missing_items_empty_list(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        lista = ListaCompras.objects.create(usuario_creacion=user1_viv)

        self.assertFalse(lista.has_missing_items())

    def test_has_missing_items_changing_list(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
            item_1,
            item_lista_1,
            item_2,
            item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        self.assertTrue(lista.has_missing_items())
        lista.buy_item(item_lista_1.id, 10)
        self.assertTrue(lista.has_missing_items())
        lista.buy_item(item_lista_2.id, 20)
        self.assertFalse(lista.has_missing_items())

    def test_rescue_items_returns_None_is_there_are_no_pending_items(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
            item_1,
            item_lista_1,
            item_2,
            item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        lista.buy_item(item_lista_1.id, 10)
        lista.buy_item(item_lista_2.id, 20)

        self.assertEqual(lista.rescue_items(user1_viv), None)

    def test_rescue_items_returns_None_is_there_are_ONLY_pending_items(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
            item_1,
            item_lista_1,
            item_2,
            item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        self.assertEqual(lista.rescue_items(user1_viv), None)

    def test_rescue_items_return_new_Lista_if_there_are_pending_items(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
            item_1,
            item_lista_1,
            item_2,
            item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        lista.buy_item(item_lista_1.id, 10)
        new_lista = lista.rescue_items(user1_viv)

        self.assertEqual(lista.get_items().count(), 1)
        self.assertEqual(new_lista.get_items().count(), 1)
        self.assertFalse(lista.get_items().first().is_pending())
        self.assertTrue(new_lista.get_items().first().is_pending())

    def test_rescue_items_doesnt_change_number_of_existing_ItemsLista(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
            item_1,
            item_lista_1,
            item_2,
            item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        original_item_count = ItemLista.objects.all().count()
        original_item_count_lista = lista.get_items().count()
        lista.buy_item(item_lista_1.id, 10)
        new_lista = lista.rescue_items(user1_viv)

        self.assertEqual(original_item_count, ItemLista.objects.all().count())
        self.assertEqual(original_item_count_lista,
                         (new_lista.get_items().count() +
                          lista.get_items().count()))

    def test_discard_items_returns_false_if_there_were_no_pending_items(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
            item_1,
            item_lista_1,
            item_2,
            item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        lista.buy_item(item_lista_1.id, 10)
        lista.buy_item(item_lista_2.id, 20)

        self.assertFalse(lista.discard_items())

    def test_discard_items_returns_True_if_there_were_missing_items(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
            item_1,
            item_lista_1,
            item_2,
            item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        lista.buy_item(item_lista_1.id, 10)

        self.assertFalse(lista.discard_items())

    def test_count_items_behaves_the_same_as_get_items_count(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        (lista,
            item_1,
            item_lista_1,
            item_2,
            item_lista_2) = get_dummy_lista_with_2_items(
            user1_viv)

        self.assertEqual(lista.get_items().count(), lista.count_items())
        lista.buy_item(item_lista_1.id, 10)
        self.assertEqual(lista.get_items().count(), lista.count_items())


class ItemListaModelTest(TestCase):

    def test_item_lista_defaults_to_0_bought(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        lista, item, item_lista = get_dummy_lista_with_1_item(user1_viv)

        self.assertEqual(item_lista.cantidad_comprada, 0)

    def test_item_lista_defaults_to_pending(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        lista, item, item_lista = get_dummy_lista_with_1_item(user1_viv)

        self.assertTrue(item_lista.is_pending())
        self.assertEqual(item_lista.estado, "pendiente")

    def test_set_done_state(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        lista, item, item_lista = get_dummy_lista_with_1_item(user1_viv)

        item_lista.set_done_state()

        self.assertFalse(item_lista.is_pending())
        self.assertEqual(item_lista.estado, "comprado")

    def test_buy_item_lista_with_0_quantity(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        lista, item, item_lista = get_dummy_lista_with_1_item(user1_viv)

        item_lista.buy(0)
        self.assertTrue(item_lista.is_pending())
        self.assertEqual(item_lista.cantidad_comprada, 0)

    def test_buy_item_lista_with_negative_quantity(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        lista, item, item_lista = get_dummy_lista_with_1_item(user1_viv)

        item_lista.buy(-10)
        self.assertTrue(item_lista.is_pending())
        self.assertEqual(item_lista.cantidad_comprada, 0)

    def test_buy_item_lista_with_positive_quantity(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        lista, item, item_lista = get_dummy_lista_with_1_item(user1_viv)

        item_lista.buy(1)
        self.assertFalse(item_lista.is_pending())
        self.assertEqual(item_lista.cantidad_comprada, 1)

    def test_buy_item_lista_that_is_already_paid(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        lista, item, item_lista = get_dummy_lista_with_1_item(user1_viv)

        item_lista.buy(1)
        self.assertFalse(item_lista.is_pending())
        self.assertEqual(item_lista.cantidad_comprada, 1)

        item_lista.buy(2)
        self.assertFalse(item_lista.is_pending())
        self.assertEqual(item_lista.cantidad_comprada, 1)
        self.assertNotEqual(item_lista.cantidad_comprada, 2)
        self.assertNotEqual(item_lista.cantidad_comprada, 3)


class EstadoGastoModelTest(TestCase):

    def test_gasto_estado_defaults_to_pendiente(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        gasto, dummy_categoria = get_dummy_gasto_pendiente(user1_viv)

        self.assertTrue(gasto.is_pending())
        self.assertFalse(gasto.is_paid())
        self.assertEqual(gasto.estado.estado, "pendiente")

    def test_is_paid(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        gasto, dummy_categoria = get_dummy_gasto_pendiente(user1_viv)
        estado_gasto, created = EstadoGasto.objects.get_or_create(
            estado="pagado")
        gasto.estado = estado_gasto

        self.assertTrue(gasto.is_paid())
        self.assertFalse(gasto.is_pending())
        self.assertEqual(gasto.estado.estado, "pagado")


class GastoModelTest(TestCase):

    def test_gasto_defaults_to_pendiente(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        gasto, dummy_categoria = get_dummy_gasto_pendiente(user1_viv)

        self.assertTrue(gasto.is_pending())
        self.assertFalse(gasto.is_paid())
        self.assertEqual(gasto.estado.estado, "pendiente")

    def test_pagar_gasto(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        gasto, dummy_categoria = get_dummy_gasto_pendiente(user1_viv)

        gasto.pagar(user1)

        self.assertTrue(gasto.is_paid())
        self.assertFalse(gasto.is_pending())
        self.assertEqual(gasto.estado.estado, "pagado")

    def test_allow_user(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        user2 = ProxyUser.objects.create(username="us2", email="b@b.com")
        gasto, dummy_categoria = get_dummy_gasto_pendiente(user1_viv)

        self.assertTrue(gasto.allow_user(user1))
        self.assertFalse(gasto.allow_user(user2))
