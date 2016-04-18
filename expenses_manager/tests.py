from django.core.urlresolvers import resolve, reverse
from django.test import TestCase
from django.http import HttpRequest
from django.template.loader import render_to_string
from expenses_manager.models import *
from django.utils import timezone
from expenses_manager.views import *


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
    item_lista = ItemLista.objects.create(
        item=item,
        lista=lista,
        cantidad_solicitada=10)
    return (lista, item, item_lista)


def get_dummy_lista_with_2_items(user_viv):
    lista, item_1, item_lista_1 = get_dummy_lista_with_1_item(user_viv)
    item_2 = Item.objects.create(nombre="test_item_2")
    item_lista_2 = ItemLista.objects.create(
        item=item_2,
        lista=lista,
        cantidad_solicitada=20)
    return lista, item_1, item_lista_1, item_2, item_lista_2


##########################
# Model Tests
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
        item_2 = Item.objects.create(nombre="test_item_2")

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
            categoria=Categoria.objects.create(nombre="dummy"),
            vivienda=correct_vivienda,
            monto=10000)

        self.assertEqual(presupuesto.get_total_expenses(), 0)

    def test_get_total_expenses_returns_0_if_there_are_no_paid_Gastos(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        dummy_categoria = Categoria.objects.create(nombre="dummy")
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
        dummy_categoria = Categoria.objects.create(nombre="dummy")
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
        dummy_categoria_1 = Categoria.objects.create(nombre="dummy1")
        dummy_categoria_2 = Categoria.objects.create(nombre="dummy2")
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
        new_item = Item.objects.create(nombre="test_item_3")

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
        new_item = Item.objects.create(nombre="test_item_3")

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

##########################
# View Tests
##########################

# view helper functions

# get test users
##################


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

# creates a vivienda with 2 users (and logs in 1 of them),
# and another vivienda with 1 user
# returns the user that is logged in, his roommate and the third one


def get_basic_setup_and_login_user_1(test):
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

    dummy_categoria = Categoria.objects.create(nombre="dummy1")
    gasto_1 = Gasto.objects.create(
        monto=111,
        creado_por=test_user_1.get_vu(),
        categoria=dummy_categoria)
    gasto_2 = Gasto.objects.create(
        monto=222,
        creado_por=test_user_2.get_vu(),
        categoria=dummy_categoria)
    gasto_3 = Gasto.objects.create(
        monto=333,
        creado_por=test_user_3.get_vu(),
        categoria=dummy_categoria)

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
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3)

# the same as get_setup_viv_2_users_viv_1_user_cat_1_gastos_3 plus 3 dummy
# items and a 2 dummy lista: one for the logged user's vivienda with items A
# and B, and one for the other vivienda with item A.
# returns the user that's logged in


def get_setup_with_gastos_items_and_listas(test):
    (test_user_1,
        test_user_2,
        test_user_3,
        dummy_categoria,
        gasto_1,
        gasto_2,
        gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
        test)
    item_1 = Item.objects.create(nombre="d1")
    item_2 = Item.objects.create(nombre="d2")
    item_3 = Item.objects.create(nombre="d3")

    lista_1 = ListaCompras.objects.create(
        usuario_creacion=test_user_1.get_vu())
    lista_2 = ListaCompras.objects.create(
        usuario_creacion=test_user_3.get_vu())

    il_1 = ItemLista.objects.create(
        item=item_1, lista=lista_1, cantidad_solicitada=1)
    il_2 = ItemLista.objects.create(
        item=item_2, lista=lista_1, cantidad_solicitada=2)

    il_3 = ItemLista.objects.create(
        item=item_1, lista=lista_2, cantidad_solicitada=3)

    return test_user_1

# check navbar
##################


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

# test basics
##################
# tests template loaded, corect html, resolves to correct view function


def test_the_basics(test, url, template_name, view_func):
    found = resolve(url)
    response = test.client.get(url, follow=True)

    test.assertTemplateUsed(response, template_name=template_name)
    test.assertEqual(found.func, view_func)

    return response

# tests the basics and checks navbar is logged out


def test_the_basics_not_logged_in(test, url, template_name, view_func):

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
    # check that i was redirected to login page
    response = test.client.get(url)

    test.assertRedirects(response, "/accounts/login/?next=" + url)

# classes
##################


class HomePageTest(TestCase):

    def test_basics_root_url(self):
        test_the_basics_not_logged_in(self, "/", "general/home.html", home)
        execute_test_the_basics_logged_in(self, "/", "general/home.html", home)

    def test_basics_home_url(self):
        test_the_basics_not_logged_in(
            self, "/home/", "general/home.html", home)
        execute_test_the_basics_logged_in(
            self, "/home/", "general/home.html", home)


class AboutPageTest(TestCase):

    def test_basics_about_url(self):
        test_the_basics_not_logged_in(
            self, "/about/", "general/about.html", about)
        execute_test_the_basics_logged_in(
            self, "/about/", "general/about.html", about)


class ErrorPageTest(TestCase):

    def test_basics_error_url(self):
        test_the_basics_not_logged_in(
            self, "/error/", "general/error.html", error)
        execute_test_the_basics_logged_in(
            self, "/error/", "general/error.html", error)


class NuevaViviendaViewTest(TestCase):

    def test_basics_nueva_vivienda_url(self):
        execute_test_the_basics_not_logged_in_restricted(
            self, "/nueva_vivienda/")
        execute_test_the_basics_logged_in(
            self,
            "/nueva_vivienda/",
            "vivienda/nueva_vivienda.html",
            nueva_vivienda)

    def test_create_new_vivienda_not_logged(self):
        response = self.client.post(
            "/nueva_vivienda/",
            data={"alias": "TestVivienda"}, follow=True)

        self.assertRedirects(
            response, "/accounts/login/?next=/nueva_vivienda/")

    def test_nueva_vivienda_has_form(self):
        test_user = get_test_user_and_login(self)
        response = self.client.get("/nueva_vivienda/")

        self.assertContains(response, "form")

    def test_create_new_vivienda(self):
        test_user = get_test_user_and_login(self)
        response = self.client.post(
            "/nueva_vivienda/",
            data={"alias": "TestVivienda"}, follow=True)

        self.assertRedirects(response, "/vivienda/")
        self.assertTrue(test_user.has_vivienda())
        self.assertContains(response, "TestVivienda")

        self.assertContains(response, "Vivienda")
        self.assertContains(response, "Gastos")
        self.assertContains(response, "Listas")
        self.assertContains(response, test_user.username)
        self.assertContains(response, "Salir")
        self.assertNotContains(response, "Crear Vivienda")
        self.assertNotContains(response, "Invitaciones")
        self.assertNotContains(response, "Entrar")


class ManageUsersViewTest(TestCase):

    def test_basics_manage_users_url(self):
        execute_test_the_basics_not_logged_in_restricted(
            self, "/manage_users/")
        execute_test_the_basics_logged_in(
            self, "/manage_users/", "vivienda/manage_users.html", manage_users)


class AbandonViewTest(TestCase):

    def test_abandon_vivienda_with_user_that_has_no_vivienda(self):
        test_user = get_test_user_and_login(self)
        self.assertFalse(test_user.has_vivienda())
        response = self.client.post(
            "/abandon/",
            data={"submit": "Abandonar vivienda"}, follow=True)
        self.assertEqual(response.status_code, 404)
        # has_logged_navbar_without_viv(self, response, test_user, 404)

    def test_abandon_vivienda_with_user_that_has_vivienda(self):
        (test_user,
            vivienda,
            test_user_viv) = get_test_user_with_vivienda_and_login(
            self)
        self.assertTrue(test_user.has_vivienda())
        self.assertEqual(test_user.get_vu().fecha_abandono, None)
        response = self.client.post(
            "/abandon/",
            data={"submit": "Abandonar vivienda"}, follow=True)
        self.assertRedirects(response, "/home/")
        self.assertEqual(test_user.get_vu(), None)
        self.assertFalse(ViviendaUsuario.objects.filter(
            estado="activo").exists())
        self.assertEqual(Vivienda.objects.all().count(), 1)
        self.assertFalse(test_user.has_vivienda())
        self.assertNotEqual(ViviendaUsuario.objects.get(
            id=test_user_viv.id).fecha_abandono, None)

        has_logged_navbar_without_viv(self, response, test_user)


class InviteListViewTest(TestCase):

    def test_basics_invite_list_url(self):
        execute_test_the_basics_not_logged_in_restricted(
            self, "/invites_list/")
        execute_test_the_basics_logged_in(
            self, "/invites_list/", "invites/invites_list.html", invites_list)


class InviteUserViewTest(TestCase):

    def test_invite_user_with_user_that_has_no_vivienda(self):
        test_user = get_test_user_and_login(self)
        response = self.client.post(
            "/invite_user/",
            data={"email": "test@test.com"}, follow=True)
        self.assertRedirects(response, "/error/")
        has_logged_navbar_without_viv(self, response, test_user)

    def test_invite_user_with_user_that_has_vivienda(self):
        (test_user,
            vivienda,
            test_user_viv) = get_test_user_with_vivienda_and_login(
            self)

        self.assertTrue(test_user.has_vivienda())

        response = self.client.post(
            "/invite_user/",
            data={"email": "test@test.com"},
            follow=True)
        self.assertRedirects(response, "/invites_list/")
        has_logged_navbar_with_viv(self, response, test_user)

        self.assertContains(response, "test@test.com")

    def test_user_accepts_invite_and_joins_vivienda(self):
        # user1 with vivienda
        test_user_1, vivienda, test_user_1_viv = get_vivienda_with_1_user()
        # user2 without vivienda logged in
        test_user_2 = get_test_user_and_login(self)
        # user1 invites user2
        invite = Invitacion.objects.create(
            invitado=test_user_2,
            invitado_por=test_user_1_viv,
            email=test_user_2.email)
        invites_in_1, invites_out_1 = test_user_1.get_invites()
        invites_in_2, invites_out_2 = test_user_2.get_invites()
        self.assertEqual(invites_in_1.count(), 0)
        self.assertEqual(invites_out_1.count(), 1)
        self.assertEqual(invites_in_2.count(), 1)
        self.assertEqual(invites_out_2.count(), 0)
        # user2 accepts
        response = self.client.post(
            "/invite/%d/" % (invite.id),
            data={"SubmitButton": "Aceptar"},
            follow=True)
        self.assertRedirects(response, "/vivienda/")
        self.assertContains(response, vivienda.alias)
        self.assertTrue(test_user_2.has_vivienda())
        self.assertTrue(test_user_1.has_vivienda())
        has_logged_navbar_with_viv(self, response, test_user_2)

    def test_user_rejects_invite_and_doesnt_join_vivienda(self):
        # user1 with vivienda
        test_user_1, vivienda, test_user_1_viv = get_vivienda_with_1_user()
        # user2 without vivienda logged in
        test_user_2 = get_test_user_and_login(self)
        # user1 invites user2
        invite = Invitacion.objects.create(
            invitado=test_user_2,
            invitado_por=test_user_1_viv,
            email=test_user_2.email)
        # user2 rejects
        response = self.client.post(
            "/invite/%d/" % (invite.id),
            data={"SubmitButton": "Declinar"},
            follow=True)
        self.assertRedirects(response, "/home/")
        self.assertNotContains(response, vivienda.alias)
        self.assertFalse(test_user_2.has_vivienda())
        self.assertTrue(test_user_1.has_vivienda())
        has_logged_navbar_without_viv(self, response, test_user_2)

    def test_user_sends_malitious_POST_to_invite_and_doesnt_join_viv(self):
        # user1 with vivienda
        test_user_1, vivienda, test_user_1_viv = get_vivienda_with_1_user()
        # user2 without vivienda logged in
        test_user_2 = get_test_user_and_login(self)
        # user1 invites user2
        invite = Invitacion.objects.create(
            invitado=test_user_2,
            invitado_por=test_user_1_viv,
            email=test_user_2.email)
        # user2 sends malitious post
        response = self.client.post(
            "/invite/%d/" % (invite.id),
            data={"SubmitButton": "SQLI"},
            follow=True)
        self.assertRedirects(response, "/error/")

        invites_in_1, invites_out_1 = test_user_1.get_invites()
        invites_in_2, invites_out_2 = test_user_2.get_invites()
        self.assertEqual(invites_in_1.count(), 0)
        self.assertEqual(invites_out_1.count(), 1)
        self.assertEqual(invites_in_2.count(), 1)
        self.assertEqual(invites_out_2.count(), 0)

        self.assertNotContains(response, vivienda.alias)
        self.assertFalse(test_user_2.has_vivienda())
        self.assertTrue(test_user_1.has_vivienda())
        has_logged_navbar_without_viv(self, response, test_user_2)

    def test_user_accepts_invite_but_has_viv_and_doesnt_join_new_viv(self):
        # user1 with vivienda
        test_user_1, vivienda_1, test_user_1_viv = get_vivienda_with_1_user()
        # user2 without vivienda logged in
        (test_user_2,
            vivienda_2,
            test_user_2_viv) = get_test_user_with_vivienda_and_login(
            self)
        # user1 invites user2
        invite = Invitacion.objects.create(
            invitado=test_user_2,
            invitado_por=test_user_1_viv,
            email=test_user_2.email)
        invites_in_1, invites_out_1 = test_user_1.get_invites()
        invites_in_2, invites_out_2 = test_user_2.get_invites()
        self.assertEqual(invites_in_1.count(), 0)
        self.assertEqual(invites_out_1.count(), 1)
        self.assertEqual(invites_in_2.count(), 1)
        self.assertEqual(invites_out_2.count(), 0)
        # user2 accepts
        response = self.client.post(
            "/invite/%d/" % (invite.id),
            data={"SubmitButton": "Aceptar"},
            follow=True)
        self.assertRedirects(response, "/error/")
        self.assertTrue(test_user_1.has_vivienda())
        self.assertEqual(test_user_1.get_vivienda().alias, vivienda_1.alias)
        self.assertTrue(test_user_2.has_vivienda())
        self.assertEqual(test_user_2.get_vivienda().alias, vivienda_2.alias)
        has_logged_navbar_with_viv(self, response, test_user_2)

    def test_user_accepts_invite_that_is_canceled_and_doesnt_join_viv(self):
        # user1 with vivienda
        test_user_1, vivienda, test_user_1_viv = get_vivienda_with_1_user()
        # user2 without vivienda logged in
        test_user_2 = get_test_user_and_login(self)
        # user1 invites user2
        invite = Invitacion.objects.create(
            invitado=test_user_2,
            invitado_por=test_user_1_viv,
            email=test_user_2.email,
            estado="cancelada")
        invites_in_1, invites_out_1 = test_user_1.get_invites()
        invites_in_2, invites_out_2 = test_user_2.get_invites()
        self.assertEqual(invites_in_1.count(), 0)
        self.assertEqual(invites_out_1.count(), 0)
        self.assertEqual(invites_in_2.count(), 0)
        self.assertEqual(invites_out_2.count(), 0)
        # user2 accepts
        response = self.client.post(
            "/invite/%d/" % (invite.id),
            data={"SubmitButton": "Aceptar"},
            follow=True)
        self.assertRedirects(response, "/error/")
        self.assertNotContains(response, vivienda.alias)
        self.assertFalse(test_user_2.has_vivienda())
        self.assertTrue(test_user_1.has_vivienda())
        has_logged_navbar_without_viv(self, response, test_user_2)

    def test_user_cancels_invite_and_other_users_cant_see_it_anymore(self):
        # user1 with vivienda logged in
        (test_user_1,
            vivienda,
            test_user_1_viv) = get_test_user_with_vivienda_and_login(
            self)
        # user2 without vivienda
        test_user_2 = get_lone_user()
        # user1 invites user2
        invite = Invitacion.objects.create(
            invitado=test_user_2,
            invitado_por=test_user_1_viv,
            email=test_user_2.email)
        # user2 cancels
        response = self.client.post(
            "/invite/%d/" % (invite.id),
            data={"SubmitButton": "Cancelar"},
            follow=True)
        # noone can see the invite anymore
        invites_in_1, invites_out_1 = test_user_1.get_invites()
        invites_in_2, invites_out_2 = test_user_2.get_invites()
        self.assertEqual(invites_in_1.count(), 0)
        self.assertEqual(invites_out_1.count(), 0)
        self.assertEqual(invites_in_2.count(), 0)
        self.assertEqual(invites_out_2.count(), 0)

        self.assertRedirects(response, "/invites_list/")
        self.assertFalse(test_user_2.has_vivienda())
        self.assertTrue(test_user_1.has_vivienda())
        has_logged_navbar_with_viv(self, response, test_user_1)


class GastoViviendaPendingListViewTest(TestCase):

    def test_basics_pending_gasto_list_url(self):
        execute_test_the_basics_not_logged_in_restricted(self, "/gastos/")

    def test_basics_with_vivienda(self):
        execute_test_basics_logged_with_viv(
            self, "/gastos/", "gastos/gastos.html", gastos)

    def test_user_must_have_vivienda(self):
        test_user = get_test_user_and_login(self)
        response = self.client.get("/gastos/", follow=True)

        self.assertRedirects(response, "/error/")
        has_logged_navbar_without_viv(self, response, test_user)

    def test_user_can_see_pending_gastos_only_of_his_vivienda(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)

        response = self.client.get("/gastos/", follow=True)
        # check that logged user can see both gastos
        self.assertContains(response, dummy_categoria.nombre)
        self.assertContains(response, gasto_1.monto)
        self.assertContains(
            response, "href=\"/detalle_gasto/%d\"" % gasto_1.id)
        self.assertContains(response, gasto_2.monto)
        self.assertContains(
            response, "href=\"/detalle_gasto/%d\"" % gasto_2.id)
        # check that logged user can't see the gasto from the other vivienda
        self.assertNotContains(response, gasto_3.monto)
        self.assertNotContains(
            response, "href=\"/detalle_gasto/%d\"" % gasto_3.id)

    def test_user_tries_to_create_new_gasto_with_incomplete_POST_request(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)

        response = self.client.post(
            "/nuevo_gasto/",
            data={"categoria": dummy_categoria, "monto": 232},
            follow=True)

        self.assertRedirects(response, "/error/")
        self.assertEqual(
            Gasto.objects.filter(
                creado_por__vivienda=test_user_1.get_vivienda()).count(),
            3)

    def test_user_can_create_pending_gasto(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)

        response = self.client.post(
            "/nuevo_gasto/",
            data={"categoria": dummy_categoria,
                  "monto": 232, "is_not_paid": ""},
            follow=True)

        self.assertRedirects(response, "/gastos/")
        pending_gastos = Gasto.objects.filter(
            creado_por__vivienda=test_user_1.get_vivienda(),
            estado__estado="pendiente")
        for gasto in pending_gastos:
            self.assertContains(response, gasto.monto)
            self.assertContains(
                response, "href=\"/detalle_gasto/%d\"" % gasto.id)
        self.assertNotContains(response, gasto_3.monto)
        self.assertNotContains(
            response, "href=\"/detalle_gasto/%d\"" % gasto_3.id)


class GastoViviendaPaidListViewTest(TestCase):

    def test_basics_paid_gasto_list_url(self):
        execute_test_the_basics_not_logged_in_restricted(self, "/gastos/")

    def test_basics__paid_gasto_list_with_vivienda(self):
        execute_test_basics_logged_with_viv(
            self, "/gastos/", "gastos/gastos.html", gastos)

    def test_user_must_have_vivienda_for_paid_gasto_list(self):
        test_user = get_test_user_and_login(self)
        response = self.client.get("/gastos/", follow=True)

        self.assertRedirects(response, "/error/")
        has_logged_navbar_without_viv(self, response, test_user)

    def test_user_can_see_paid_gastos_only_of_his_vivienda(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)
        gasto_1.pagar(test_user_1)
        gasto_2.pagar(test_user_2)
        gasto_3.pagar(test_user_3)

        response = self.client.get("/gastos/", follow=True)
        # check that logged user can see both gastos
        self.assertContains(response, dummy_categoria.nombre)
        self.assertContains(response, gasto_1.monto)
        self.assertContains(
            response, "href=\"/detalle_gasto/%d\"" % gasto_1.id)
        self.assertContains(response, gasto_2.monto)
        self.assertContains(
            response, "href=\"/detalle_gasto/%d\"" % gasto_2.id)
        # check that logged user can't see the gasto from the other vivienda
        self.assertNotContains(response, gasto_3.monto)
        self.assertNotContains(
            response, "href=\"/detalle_gasto/%d\"" % gasto_3.id)

    def test_user_can_create_paid_gasto(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)
        response = self.client.post(
            "/nuevo_gasto/",
            data={"categoria": dummy_categoria, "monto": 232, "is_paid": ""},
            follow=True)

        self.assertRedirects(response, "/gastos/")
        paid_gastos = Gasto.objects.filter(
            creado_por__vivienda=test_user_1.get_vivienda(),
            estado__estado="pagado")
        for gasto in paid_gastos:
            self.assertContains(response, gasto.monto)
            self.assertContains(
                response, "href=\"/detalle_gasto/%d\"" % gasto.id)
        self.assertNotContains(response, gasto_3.monto)
        self.assertNotContains(
            response, "href=\"/detalle_gasto/%d\"" % gasto_3.id)


class GastoViviendaPayViewTest(TestCase):

    def test_not_logged_user_cant_see_gasto(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)
        self.client.logout()
        response = self.client.get(
            "/detalle_gasto/%d/" % (gasto_1.id),
            follow=True)
        self.assertRedirects(
            response,
            "/accounts/login/?next=/detalle_gasto/%d/" % (gasto_1.id))
        has_not_logged_navbar(self, response)

    def test_not_logged_user_cant_pay_gasto(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)
        self.client.logout()
        response = self.client.post(
            "/detalle_gasto/%d/" % (gasto_1.id),
            data={"csrfmiddlewaretoken": "rubbish"},
            follow=True)
        self.assertRedirects(
            response,
            "/accounts/login/?next=/detalle_gasto/%d/" % (gasto_1.id))
        has_not_logged_navbar(self, response)

    def test_outside_user_cant_see_gasto(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)
        response = self.client.get(
            "/detalle_gasto/%d/" % (gasto_3.id),
            follow=True)
        self.assertRedirects(response, "/error/")
        self.assertNotContains(
            response, "href=\"/detalle_gasto/%d\"" % gasto_3.id)

    def test_outside_user_cant_pay_gasto(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)
        response = self.client.post(
            "/detalle_gasto/%d/" % (gasto_3.id),
            data={"csrfmiddlewaretoken": "rubbish"},
            follow=True)
        self.assertRedirects(response, "/error/")
        self.assertNotContains(
            response, "href=\"/detalle_gasto/%d\"" % gasto_3.id)

    def test_user_can_pay_pending_gasto(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)
        response = self.client.post(
            "/detalle_gasto/%d/" % (gasto_1.id),
            data={"submit": "submit"},
            follow=True)
        self.assertRedirects(response, "/detalle_gasto/%d/" % (gasto_1.id))
        self.assertEqual(
            Gasto.objects.filter(
                creado_por__vivienda=test_user_1.get_vivienda(),
                estado__estado="pendiente")
            .count(),
            1)
        self.assertEqual(
            Gasto.objects.filter(
                creado_por__vivienda=test_user_1.get_vivienda(),
                estado__estado="pagado")
            .count(),
            1)
        self.assertNotContains(response, "<a href=\"/detalle_lista/")
        self.assertNotContains(response, "<td><b>Lista compras:</b></td>")

    def test_user_cannot_pay_paid_gasto(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)
        gasto_1.pagar(test_user_1)
        self.assertTrue(gasto_1.is_paid())
        response = self.client.post(
            "/detalle_gasto/%d/" % (gasto_1.id),
            data={"submit": "submit"},
            follow=True)
        self.assertRedirects(response, "/error/")
        self.assertEqual(
            Gasto.objects.filter(
                creado_por__vivienda=test_user_1.get_vivienda(),
                estado__estado="pendiente")
            .count(),
            1)
        self.assertEqual(
            Gasto.objects.filter(
                creado_por__vivienda=test_user_1.get_vivienda(),
                estado__estado="pagado")
            .count(),
            1)

    def test_roommate_can_pay_pending_gasto(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)
        response = self.client.post(
            "/detalle_gasto/%d/" % (gasto_2.id),
            data={"submit": "submit"},
            follow=True)
        self.assertRedirects(response, "/detalle_gasto/%d/" % (gasto_2.id))
        self.assertEqual(
            Gasto.objects.filter(
                creado_por__vivienda=test_user_1.get_vivienda(),
                estado__estado="pendiente")
            .count(),
            1)
        self.assertEqual(
            Gasto.objects.filter(
                creado_por__vivienda=test_user_1.get_vivienda(),
                estado__estado="pagado")
            .count(),
            1)
        self.assertNotContains(response, "<a href=\"/detalle_lista/")
        self.assertNotContains(response, "<td><b>Lista compras:</b></td>")

    def test_roommate_cannot_pay_paid_gasto(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)
        gasto_2.pagar(test_user_2)
        self.assertTrue(gasto_2.is_paid())
        response = self.client.post(
            "/detalle_gasto/%d/" % (gasto_2.id),
            data={"submit": "submit"},
            follow=True)
        self.assertRedirects(response, "/error/")
        self.assertEqual(
            Gasto.objects.filter(
                creado_por__vivienda=test_user_1.get_vivienda(),
                estado__estado="pendiente")
            .count(),
            1)
        self.assertEqual(
            Gasto.objects.filter(
                creado_por__vivienda=test_user_1.get_vivienda(),
                estado__estado="pagado")
            .count(),
            1)


class GastoGraphsTest(TestCase):

    url = "/graphs/gastos/"

    def test_not_logged_user_cant_see_gasto_graph(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)
        self.client.logout()
        response = self.client.get(
            self.url,
            follow=True)
        self.assertRedirects(
            response,
            "/accounts/login/?next=%s" % (self.url))
        has_not_logged_navbar(self, response)

    def test_homeless_user_cant_see_gasto_graph(self):
        test_user = get_test_user_and_login(self)
        response = self.client.get(
            self.url,
            follow=True)

        self.assertRedirects(response, "/error/")
        has_logged_navbar_without_viv(self, response, test_user)

    def test_user_can_see_graphs(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)
        response = self.client.get(
            self.url,
            follow=True)
        self.assertContains(response, "canvas")
        self.assertContains(response, dummy_categoria.nombre)


class ListaPendingViewTest(TestCase):

    def test_basic_setup(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        vivienda = test_user.get_vivienda()

        self.assertEqual(
            ListaCompras.objects.filter(
                usuario_creacion__vivienda=vivienda).count(),
            1)
        self.assertEqual(
            ListaCompras.objects.count(),
            2)
        self.assertEqual(
            ItemLista.objects.filter(
                lista=ListaCompras.objects.get(
                    usuario_creacion__vivienda=vivienda))
            .count(),
            2)
        self.assertEqual(
            ItemLista.objects.filter(
                lista=ListaCompras.objects.exclude(
                    usuario_creacion__vivienda=vivienda).first())
            .count(),
            1)
        self.assertEqual(Item.objects.count(), 3)

    def test_not_logged_user_cant_see_lista(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        self.client.logout()
        lista = ListaCompras.objects.get(
            usuario_creacion__vivienda=test_user.get_vivienda())
        response = self.client.get(
            "/lists/",
            follow=True)
        self.assertRedirects(response, "/accounts/login/?next=/lists/")
        self.assertNotContains(response, "<td>%d</td>" % (lista.count_items()))
        self.assertNotContains(response, "<td>%s</td>" %
                               (lista.usuario_creacion.user))

    def test_outsider_user_cant_see_lista(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        lista = ListaCompras.objects.exclude(
            usuario_creacion__vivienda=test_user.get_vivienda()).first()
        response = self.client.get(
            "/lists/",
            follow=True)
        self.assertNotContains(response, "<td>%d</td>" % (lista.count_items()))
        self.assertNotContains(response, "<td>%s</td>" %
                               (lista.usuario_creacion.user))

    def test_logged_user_with_no_vivienda_cant_see_any_lista(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        lista = ListaCompras.objects.get(
            usuario_creacion__vivienda=test_user.get_vivienda())
        test_user.get_vu().leave()
        response = self.client.get(
            "/lists/",
            follow=True)
        self.assertRedirects(response, "/error/")
        self.assertNotContains(response, "<td>%d</td>" % (lista.count_items()))
        self.assertNotContains(response, "<td>%s</td>" %
                               (lista.usuario_creacion.user))

    def test_logged_user_can_see_pending_listas_of_his_vivienda(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        lista = ListaCompras.objects.get(
            usuario_creacion__vivienda=test_user.get_vivienda())
        response = self.client.get(
            "/lists/",
            follow=True)
        self.assertContains(response, "<td>%d</td>" % (lista.count_items()))
        self.assertContains(response, "<td>%s</td>" %
                            (lista.usuario_creacion.user))

    def test_logged_user_cant_see_pending_listas_of_other_viviendas(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        lista = ListaCompras.objects.exclude(
            usuario_creacion__vivienda=test_user.get_vivienda()).first()
        response = self.client.get(
            "/lists/",
            follow=True)
        self.assertNotContains(response, "<td>%d</td>" % (lista.count_items()))
        self.assertNotContains(response, "<td>%s</td>" %
                               (lista.usuario_creacion.user))

    def test_logged_user_cant_see_pending_listas_of_past_viviendas(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        original_vivienda_lista = ListaCompras.objects.get(
            usuario_creacion__vivienda=test_user.get_vivienda())
        new_vivienda_lista = ListaCompras.objects.exclude(
            usuario_creacion__vivienda=test_user.get_vivienda()).first()
        # user leaves
        test_user.get_vu().leave()
        self.assertFalse(test_user.has_vivienda())
        # user joins other vivienda
        test_user_new_viv = ViviendaUsuario.objects.create(
            user=test_user,
            vivienda=new_vivienda_lista.usuario_creacion.vivienda)
        self.assertTrue(test_user.has_vivienda())

        # user goes to /lists/
        response = self.client.get(
            "/lists/",
            follow=True)

        # user can see list of vivienda 2
        self.assertContains(response, "<td>%d</td>" %
                            (new_vivienda_lista.count_items()))
        self.assertContains(response, "<td>%s</td>" %
                            (new_vivienda_lista.usuario_creacion.user))
        # user cant see list of vivienda 1
        self.assertNotContains(response, "<td>%d</td>" %
                               (original_vivienda_lista.count_items()))
        self.assertNotContains(response, "<td>%s</td>" %
                               (original_vivienda_lista.usuario_creacion.user))


class NewListaViewTest(TestCase):

    def test_not_logged_user_cant_create_lista(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        self.client.logout()
        response = self.client.post(
            "/nueva_lista/",
            data={
                "csrfmiddlewaretoken": "rubbish",
                "max_item_index": 2,
                "item_1": "d1",
                "quantity_1": 10,
                "item_2": "d2",
                "quantity_2": 20
            },
            follow=True)
        self.assertRedirects(response, "/accounts/login/?next=/nueva_lista/")

    def test_logged_user_with_no_vivienda_cant_create_lista(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        test_user.get_vu().leave()
        response = self.client.post(
            "/nueva_lista/",
            data={
                "csrfmiddlewaretoken": "rubbish",
                "max_item_index": 2,
                "item_1": "d1",
                "quantity_1": 10,
                "item_2": "d2",
                "quantity_2": 20
            },
            follow=True)
        self.assertRedirects(response, "/error/")

    def test_user_cant_create_empty_lista(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        response = self.client.post(
            "/nueva_lista/",
            data={
                "csrfmiddlewaretoken": "rubbish",
                "max_item_index": 0
            },
            follow=True)
        self.assertRedirects(response, "/error/")

        response = self.client.post(
            "/nueva_lista/",
            data={
                "csrfmiddlewaretoken": "rubbish",
                "max_item_index": 2
            },
            follow=True)
        self.assertRedirects(response, "/lists/")

    def test_user_can_create_lista_simple(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        response = self.client.post(
            "/nueva_lista/",
            data={
                "csrfmiddlewaretoken": "rubbish",
                "max_item_index": 3,
                "item_1": "d1",
                "quantity_1": 10,
                "item_2": "d2",
                "quantity_2": 20,
                "item_3": "d3",
                "quantity_3": 30
            },
            follow=True)

        self.assertEqual(
            ListaCompras.objects.filter(
                usuario_creacion__vivienda=test_user.get_vivienda()).count(),
            2)
        self.assertEqual(
            ListaCompras.objects.count(),
            3)
        lista = ListaCompras.objects.latest("fecha")
        self.assertRedirects(response, "/detalle_lista/%d/" % (lista.id))
        for item_lista in ItemLista.objects.filter(lista=lista):
            self.assertContains(
                response,
                "<td class=\"cantidad_solicitada\">%d (%s)</td>" % (
                    item_lista.cantidad_solicitada,
                    item_lista.item.unidad_medida))

    def test_user_can_create_lista_w_items_that_skip_index_numbers(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        response = self.client.post(
            "/nueva_lista/",
            data={
                "csrfmiddlewaretoken": "rubbish",
                "max_item_index": 3,
                "item_1": "d1",
                "quantity_1": 10,
                "item_3": "d3",
                "quantity_3": 30
            },
            follow=True)

        lista = ListaCompras.objects.latest("fecha")
        self.assertEqual(
            lista.count_items(),
            2)
        self.assertRedirects(response, "/detalle_lista/%d/" % (lista.id))
        for item_lista in ItemLista.objects.filter(lista=lista):
            self.assertContains(
                response,
                "<td class=\"cantidad_solicitada\">%d (%s)</td>" % (
                    item_lista.cantidad_solicitada,
                    item_lista.item.unidad_medida))

    def test_user_can_create_lista_w_skip_item_and_empty_fields(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        response = self.client.post(
            "/nueva_lista/",
            data={
                "csrfmiddlewaretoken": "rubbish",
                "max_item_index": 3,
                "item_1": "d1",
                "quantity_1": 10,
                "item_2": "",
                "quantity_2": 2,
                "item_3": "d3",
                "quantity_3": 30
            },
            follow=True)

        lista = ListaCompras.objects.latest("fecha")
        self.assertEqual(
            lista.count_items(),
            2)
        self.assertRedirects(response, "/detalle_lista/%d/" % (lista.id))
        for item_lista in ItemLista.objects.filter(lista=lista):
            self.assertContains(
                response,
                "<td class=\"cantidad_solicitada\">%d (%s)</td>" % (
                    item_lista.cantidad_solicitada,
                    item_lista.item.unidad_medida))

    def test_user_cant_create_lista_with_repeated_items(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        response = self.client.post(
            "/nueva_lista/",
            data={
                "csrfmiddlewaretoken": "rubbish",
                "max_item_index": 3,
                "item_1": "d1",
                "quantity_1": 10,
                "item_2": "d2",
                "quantity_2": 20,
                "item_3": "d1",
                "quantity_3": 30
            },
            follow=True)
        self.assertRedirects(response, "/lists/")
        # TODO the following tests
        # self.assertContains(response,
        # "La lista no puede contener varias veces el mismo item!")


class PayListaViewTest(TestCase):

    # basics
    def test_not_logged_user_cant_pay_lista(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        lista = ListaCompras.objects.filter(
            usuario_creacion__vivienda=test_user.get_vivienda()).first()
        self.client.logout()
        # tries to pay whole lista
        response = self.client.post(
            "/detalle_lista/%d/" % (lista.id),
            data={
                "csrfmiddlewaretoken": "rubbish",
                "max_item_index": 2,
                "item_1": "d1",
                "quantity_1": 10,
                "item_2": "d2",
                "quantity_2": 20
            },
            follow=True)
        self.assertRedirects(
            response, "/accounts/login/?next=/detalle_lista/%d/" % (lista.id))

    def test_outsider_user_cant_pay_lista(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        not_my_lista = ListaCompras.objects.exclude(
            usuario_creacion__vivienda=test_user.get_vivienda()).first()
        # tries to pay whole lista
        response = self.client.post(
            "/detalle_lista/%d/" % (not_my_lista.id),
            data={
                "csrfmiddlewaretoken": "rubbish",
                "max_item_index": 2,
                "item_1": "d1",
                "quantity_1": 10,
                "item_2": "d2",
                "quantity_2": 20
            },
            follow=True)
        self.assertRedirects(response, "/error/")

    def test_past_user_cant_pay_lista(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        lista = ListaCompras.objects.filter(
            usuario_creacion__vivienda=test_user.get_vivienda()).first()
        test_user.get_vu().leave()
        # tries to pay whole lista
        response = self.client.post(
            "/detalle_lista/%d/" % (lista.id),
            data={
                "csrfmiddlewaretoken": "rubbish",
                "max_item_index": 2,
                "item_1": "d1",
                "quantity_1": 10,
                "item_2": "d2",
                "quantity_2": 20
            },
            follow=True)
        self.assertRedirects(response, "/error/")

    # paying no recicle
    def test_user_can_pay_lista_no_recicle(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        lista = ListaCompras.objects.filter(
            usuario_creacion__vivienda=test_user.get_vivienda()).first()
        [item_lista_1, item_lista_2] = lista.get_items()
        # pays half lista no recicle
        response = self.client.post(
            "/detalle_lista/%d/" % (lista.id),
            data={
                "csrfmiddlewaretoken": "rubbish",
                "descartar_items": "checked",
                "monto_total": 1000,
                str(item_lista_1.id): 1,
                str(item_lista_2.id): 2
            },
            follow=True)
        gasto = Gasto.objects.latest("fecha_creacion")
        self.assertRedirects(response, "/detalle_gasto/%d/" % (gasto.id))

    def test_user_cant_pay_lista_without_monto_no_recicle(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        lista = ListaCompras.objects.filter(
            usuario_creacion__vivienda=test_user.get_vivienda()).first()
        [item_lista_1, item_lista_2] = lista.get_items()
        # pays half lista no recicle
        response = self.client.post(
            "/detalle_lista/%d/" % (lista.id),
            data={
                "csrfmiddlewaretoken": "rubbish",
                "descartar_items": "checked",
                str(item_lista_1.id): 1,
                str(item_lista_2.id): 2
            },
            follow=True)
        self.assertRedirects(response, "/error/")

    def test_user_cant_pay_lista_without_items_selected_no_recicle(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        lista = ListaCompras.objects.filter(
            usuario_creacion__vivienda=test_user.get_vivienda()).first()
        # pays half lista no recicle
        response = self.client.post(
            "/detalle_lista/%d/" % (lista.id),
            data={
                "csrfmiddlewaretoken": "rubbish",
                "descartar_items": "checked",
                "monto_total": 1000
            },
            follow=True)
        self.assertRedirects(response, "/error/")

    # paying with recicle
    def test_user_can_pay_lista_with_recicle(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        lista = ListaCompras.objects.filter(
            usuario_creacion__vivienda=test_user.get_vivienda()).first()
        [item_lista_1, item_lista_2] = lista.get_items()
        # pays half lista no recicle
        response = self.client.post(
            "/detalle_lista/%d/" % (lista.id),
            data={
                "csrfmiddlewaretoken": "rubbish",
                "rescatar_items": "checked",
                "monto_total": 1000,
                str(item_lista_2.id): 2
            },
            follow=True)
        gasto = Gasto.objects.latest("fecha_creacion")
        self.assertRedirects(response, "/detalle_gasto/%d/" % (gasto.id))

        # old lista only has item_2, and is paid
        self.assertEqual(lista.get_items().count(), 1)
        self.assertEqual(
            lista.get_items().first().item.nombre,
            item_lista_2.item.nombre)
        self.assertTrue(ListaCompras.objects.get(id=lista.id).is_done())
        # created new lista with item_1
        new_lista = ListaCompras.objects.latest("fecha")
        self.assertEqual(new_lista.get_items().count(), 1)
        self.assertEqual(
            new_lista.get_items().first().item.nombre,
            item_lista_1.item.nombre)
        self.assertFalse(new_lista.is_done())

    def test_user_paying_full_lista_doesnt_create_a_Lista_with_recicle(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        lista = ListaCompras.objects.filter(
            usuario_creacion__vivienda=test_user.get_vivienda()).first()
        [item_lista_1, item_lista_2] = lista.get_items()
        original_lista_count = ListaCompras.objects.count()
        original_gasto_count = Gasto.objects.count()
        # pays half lista no recicle
        response = self.client.post(
            "/detalle_lista/%d/" % (lista.id),
            data={
                "csrfmiddlewaretoken": "rubbish",
                "rescatar_items": "checked",
                "monto_total": 1000,
                str(item_lista_1.id): 1,
                str(item_lista_2.id): 2
            },
            follow=True)
        self.assertEqual(
            Gasto.objects.count(),
            original_gasto_count + 1)
        gasto = Gasto.objects.latest("fecha_creacion")
        self.assertRedirects(response, "/detalle_gasto/%d/" % (gasto.id))

        # created new lista with item_2
        self.assertEqual(original_lista_count, ListaCompras.objects.count())
        # old lista only has both items, and is paid
        self.assertEqual(lista.get_items().count(), 2)
        self.assertTrue(ListaCompras.objects.get(id=lista.id).is_done())

    def test_user_cant_pay_lista_without_monto_with_recicle(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        lista = ListaCompras.objects.filter(
            usuario_creacion__vivienda=test_user.get_vivienda()).first()
        [item_lista_1, item_lista_2] = lista.get_items()
        original_lista_count = ListaCompras.objects.count()
        original_gasto_count = Gasto.objects.count()
        # pays half lista no recicle
        response = self.client.post(
            "/detalle_lista/%d/" % (lista.id),
            data={
                "csrfmiddlewaretoken": "rubbish",
                "rescatar_items": "checked",
                str(item_lista_1.id): 1,
                str(item_lista_2.id): 2
            },
            follow=True)
        self.assertRedirects(response, "/error/")
        self.assertEqual(ListaCompras.objects.count(), original_lista_count)
        self.assertEqual(Gasto.objects.count(), original_gasto_count)
        self.assertFalse(ListaCompras.objects.get(id=lista.id).is_done())

    def test_user_cant_pay_lista_without_items_selected_with_recicle(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        lista = ListaCompras.objects.filter(
            usuario_creacion__vivienda=test_user.get_vivienda()).first()
        [item_lista_1, item_lista_2] = lista.get_items()
        original_lista_count = ListaCompras.objects.count()
        original_gasto_count = Gasto.objects.count()
        # pays half lista no recicle
        response = self.client.post(
            "/detalle_lista/%d/" % (lista.id),
            data={
                "csrfmiddlewaretoken": "rubbish",
                "rescatar_items": "checked",
                "monto_total": 1000
            },
            follow=True)
        self.assertRedirects(response, "/error/")
        self.assertEqual(ListaCompras.objects.count(), original_lista_count)
        self.assertEqual(Gasto.objects.count(), original_gasto_count)
        self.assertFalse(ListaCompras.objects.get(id=lista.id).is_done())


class PresupuestoViewTest(TestCase):

    def test_basics_presupuesto_list_url(self):
        execute_test_the_basics_not_logged_in_restricted(
            self, "/presupuestos/")
        execute_test_basics_logged_with_viv(
            self, "/presupuestos/", "vivienda/presupuestos.html", presupuestos)

    def test_not_logged_user_cant_see_presupuestos(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        presupuesto = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=12345)

        self.client.logout()
        response = self.client.get(
            "/presupuestos/",
            follow=True)

        self.assertRedirects(response, "/accounts/login/?next=/presupuestos/")
        self.assertNotContains(response, "<td>%d</td>" % (presupuesto.monto))

    def test_homeless_user_cant_see_presupuestos(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        presupuesto = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=12345)
        test_user.get_vu().leave()
        response = self.client.get(
            "/presupuestos/",
            follow=True)
        self.assertRedirects(response, "/error/")
        self.assertNotContains(response, "<td>%d</td>" % (presupuesto.monto))
        self.assertContains(
            response,
            "Para tener acceso a esta página debe pertenecer a una vivienda")

    def test_outsider_cant_see_presupuestos_of_vivienda(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        other_vivienda = Vivienda.objects.exclude(
            id=test_user.get_vivienda().id).first()
        my_presupuesto = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=123)

        other_presupuesto = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=other_vivienda,
            monto=321)
        response = self.client.get(
            "/presupuestos/",
            follow=True)

        self.assertNotContains(response, "<td>$ %d</td>" %
                               (other_presupuesto.monto))
        self.assertContains(response, "<td>$ %d</td>" % (my_presupuesto.monto))

    def test_past_user_cant_see_presupuestos_of_old_vivienda(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        presupuesto_old = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=123)
        test_user.get_vu().leave()
        new_vivienda = Vivienda.objects.create(alias="my_new_viv")
        new_viv_usuario = ViviendaUsuario.objects.create(
            user=test_user, vivienda=new_vivienda)
        presupuesto_new = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=321)
        response = self.client.get(
            "/presupuestos/",
            follow=True)

        self.assertNotContains(response, "<td>$ %d</td>" %
                               (presupuesto_old.monto))
        self.assertContains(response, "<td>$ %d</td>" %
                            (presupuesto_new.monto))

    def test_url_without_period_redirects_to_current_period(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)
        next_year, next_month = this_period.get_next_period()
        next_period, __ = YearMonth.objects.get_or_create(
            year=next_year, month=next_month)
        presupuesto_now = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=this_period,
            monto=12345)

        response = self.client.get(
            "/presupuestos/",
            follow=True)

        self.assertRedirects(
            response,
            "/presupuestos/%d/%d" % (this_period.year, this_period.month))

    def test_logged_user_can_see_presupuestos_for_current_period_only(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)
        next_year, next_month = this_period.get_next_period()
        next_period, __ = YearMonth.objects.get_or_create(
            year=next_year, month=next_month)
        presupuesto_now = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=this_period,
            monto=123)

        presupuesto_next = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=next_period,
            monto=321)
        response = self.client.get(
            "/presupuestos/",
            follow=True)

        self.assertNotContains(response, "<td>$ %d</td>" %
                               (presupuesto_next.monto))
        self.assertContains(response, "<td>$ %d</td>" %
                            (presupuesto_now.monto))

    def test_logged_user_can_see_link_to_next_period(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)
        next_year, next_month = this_period.get_next_period()
        next_period, __ = YearMonth.objects.get_or_create(
            year=next_year, month=next_month)
        presupuesto_now = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=this_period,
            monto=12345)

        presupuesto_next = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=next_period,
            monto=54321)
        response = self.client.get(
            "/presupuestos/",
            follow=True)
        self.assertContains(response, "<a href=\"/presupuestos/%d/%d\"" %
                            (next_year, next_month))

    def test_logged_user_can_see_link_to_previous_period(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)
        prev_year, prev_month = this_period.get_prev_period()
        prev_period, __ = YearMonth.objects.get_or_create(
            year=prev_year, month=prev_month)
        presupuesto_now = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=this_period,
            monto=12345)

        presupuesto_prev = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=prev_period,
            monto=54321)
        response = self.client.get(
            "/presupuestos/",
            follow=True)
        self.assertContains(response, "<a href=\"/presupuestos/%d/%d\"" %
                            (prev_period.year, prev_period.month))

    def test_logged_user_can_see_link_to_create_new_presupuesto(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)
        next_year, next_month = this_period.get_next_period()
        next_period, __ = YearMonth.objects.get_or_create(
            year=next_year, month=next_month)
        presupuesto_now = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=this_period,
            monto=12345)

        presupuesto_next = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=next_period,
            monto=54321)
        response = self.client.get(
            "/presupuestos/",
            follow=True)

        self.assertContains(response, "href=\"/presupuestos/new/\"")

    def test_logged_user_can_see_link_to_modify_presupuesto(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)
        next_year, next_month = this_period.get_next_period()
        next_period, __ = YearMonth.objects.get_or_create(
            year=next_year, month=next_month)
        presupuesto_now = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=this_period,
            monto=12345)

        presupuesto_next = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=next_period,
            monto=54321)
        response = self.client.get(
            "/presupuestos/",
            follow=True)

        self.assertContains(
            response,
            "href=\"/presupuestos/%d/%d/%s\">" % (
                presupuesto_now.year_month.year,
                presupuesto_now.year_month.month,
                presupuesto_now.categoria))

    def test_user_can_see_presupuestos_for_any_categoria_in_this_period(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)
        next_year, next_month = this_period.get_next_period()
        next_period, __ = YearMonth.objects.get_or_create(
            year=next_year, month=next_month)
        presupuesto_cat1 = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=this_period,
            monto=12345)

        presupuesto_cat2 = Presupuesto.objects.create(
            categoria=Categoria.objects.create(nombre="dummy2"),
            vivienda=test_user.get_vivienda(),
            year_month=this_period,
            monto=54321)
        response = self.client.get(
            "/presupuestos/",
            follow=True)

        self.assertContains(response, "<td>%s</td>" %
                            (presupuesto_cat1.categoria))
        self.assertContains(response, "<td>%s</td>" %
                            (presupuesto_cat2.categoria))


class PresupuestoGraphsTest(TestCase):

    url = "/graphs/presupuestos/"

    def test_basics_presupuesto_graph_url(self):
        execute_test_the_basics_not_logged_in_restricted(
            self, self.url)
        execute_test_basics_logged_with_viv(
            self,
            self.url,
            "vivienda/graphs/presupuestos.html",
            graphs_presupuestos)

    def test_not_logged_user_cant_see_presupuestos_graph(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        presupuesto = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=12345)

        self.client.logout()
        response = self.client.get(
            self.url,
            follow=True)

        self.assertRedirects(
            response,
            "/accounts/login/?next=%s" % (self.url))
        self.assertNotContains(
            response,
            presupuesto.categoria)

    def test_homeless_user_cant_see_presupuestos_graph(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        presupuesto = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=12345)
        test_user.get_vu().leave()
        response = self.client.get(
            self.url,
            follow=True)
        self.assertRedirects(response, "/error/")
        self.assertNotContains(
            response,
            presupuesto.categoria)
        self.assertContains(
            response,
            "Para tener acceso a esta página debe pertenecer a una vivienda")

    def test_outsider_cant_see_presupuesto_graphs_of_vivienda(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        other_vivienda = Vivienda.objects.exclude(
            id=test_user.get_vivienda().id).first()
        my_presupuesto = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=12345)

        other_presupuesto = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=other_vivienda,
            monto=54321)
        response = self.client.get(
            self.url,
            follow=True)

        self.assertNotContains(response, other_presupuesto.monto)
        self.assertContains(response, my_presupuesto.monto)

    def test_past_user_cant_see_presupuestos_graphs_of_old_vivienda(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        presupuesto_old = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=12345)
        test_user.get_vu().leave()
        new_vivienda = Vivienda.objects.create(alias="my_new_viv")
        new_viv_usuario = ViviendaUsuario.objects.create(
            user=test_user, vivienda=new_vivienda)
        presupuesto_new = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=54321)
        response = self.client.get(
            self.url,
            follow=True)

        self.assertNotContains(response, presupuesto_old.monto)
        self.assertContains(response, presupuesto_new.monto)

    def test_url_without_period_redirects_to_current_period_graph(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)
        next_year, next_month = this_period.get_next_period()
        next_period, __ = YearMonth.objects.get_or_create(
            year=next_year, month=next_month)
        presupuesto_now = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=this_period,
            monto=12345)

        response = self.client.get(
            self.url,
            follow=True)

        self.assertRedirects(
            response,
            "%s%d/%d" % (self.url, this_period.year, this_period.month))

    def test_user_can_see_presupuestos_graph_for_current_period_only(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)
        next_year, next_month = this_period.get_next_period()
        next_period, __ = YearMonth.objects.get_or_create(
            year=next_year, month=next_month)
        presupuesto_now = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=this_period,
            monto=12345)

        presupuesto_next = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=next_period,
            monto=54321)
        response = self.client.get(
            self.url,
            follow=True)

        self.assertNotContains(response, presupuesto_next.monto)
        self.assertContains(response, presupuesto_now.monto)

    def test_logged_user_can_see_link_to_next_period(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)
        next_year, next_month = this_period.get_next_period()
        next_period, __ = YearMonth.objects.get_or_create(
            year=next_year, month=next_month)
        presupuesto_now = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=this_period,
            monto=12345)

        presupuesto_next = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=next_period,
            monto=54321)
        response = self.client.get(
            self.url,
            follow=True)
        self.assertContains(response, "<a href=\"%s%d/%d\"" %
                            (self.url, next_year, next_month))

    def test_logged_user_can_see_link_to_previous_period(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)
        prev_year, prev_month = this_period.get_prev_period()
        prev_period, __ = YearMonth.objects.get_or_create(
            year=prev_year, month=prev_month)
        presupuesto_now = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=this_period,
            monto=12345)

        presupuesto_prev = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=prev_period,
            monto=54321)
        response = self.client.get(
            self.url,
            follow=True)
        self.assertContains(response, "<a href=\"%s%d/%d\"" %
                            (self.url, prev_period.year, prev_period.month))

    def test_logged_user_can_see_link_to_create_new_presupuesto(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)
        next_year, next_month = this_period.get_next_period()
        next_period, __ = YearMonth.objects.get_or_create(
            year=next_year, month=next_month)
        presupuesto_now = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=this_period,
            monto=12345)

        presupuesto_next = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=next_period,
            monto=54321)
        response = self.client.get(
            self.url,
            follow=True)

        self.assertContains(response, "href=\"/presupuestos/new/\"")

    def test_logged_user_can_see_link_to_modify_presupuesto(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)
        next_year, next_month = this_period.get_next_period()
        next_period, __ = YearMonth.objects.get_or_create(
            year=next_year, month=next_month)
        presupuesto_now = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=this_period,
            monto=12345)

        presupuesto_next = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=next_period,
            monto=54321)
        response = self.client.get(
            self.url,
            follow=True)

        self.assertContains(
            response,
            "href=\"/presupuestos/%d/%d/%s\">" % (
                presupuesto_now.year_month.year,
                presupuesto_now.year_month.month,
                presupuesto_now.categoria))

    def test_user_can_see_presupuestos_for_any_categoria_in_this_period(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)
        next_year, next_month = this_period.get_next_period()
        next_period, __ = YearMonth.objects.get_or_create(
            year=next_year, month=next_month)
        presupuesto_cat1 = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            year_month=this_period,
            monto=12345)

        presupuesto_cat2 = Presupuesto.objects.create(
            categoria=Categoria.objects.create(nombre="dummy2"),
            vivienda=test_user.get_vivienda(),
            year_month=this_period,
            monto=54321)
        response = self.client.get(
            self.url,
            follow=True)

        self.assertContains(response, presupuesto_cat1.categoria)
        self.assertContains(response, presupuesto_cat2.categoria)


class NuevoPresupuestoViewTest(TestCase):

    def test_not_logged_user_cant_create_presupuesto(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        categoria = Categoria.objects.all().first()
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)

        self.client.logout()

        response = self.client.post(
            "/presupuestos/new/",
            data={
                "categoria": categoria.nombre,
                "year_month": this_period.id,
                "monto": 10000
            },
            follow=True)
        self.assertRedirects(
            response,
            "/accounts/login/?next=/presupuestos/new/")

    def test_homeless_user_cant_create_presupuesto(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        categoria = Categoria.objects.all().first()
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)

        test_user.get_vu().leave()

        response = self.client.post(
            "/presupuestos/new/",
            data={
                "categoria": categoria.nombre,
                "year_month": this_period.id,
                "monto": 10000
            },
            follow=True)
        self.assertRedirects(
            response,
            "/error/")
        self.assertContains(
            response,
            "Para ver esta página debe pertenecer a una vivienda")

    def test_user_can_see_form(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        response = self.client.get(
            "/presupuestos/new/",
            follow=True)

        self.assertContains(response, "form")
        self.assertContains(response, "action=\"\"")

    def test_user_cant_create_new_presupuesto_if_POST_is_broken(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        categoria = Categoria.objects.all().first()
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)

        self.assertEqual(Presupuesto.objects.count(), 0)

        response = self.client.post(
            "/presupuestos/new/",
            data={
                "categoria": categoria.nombre,
                "year_month": this_period.id
            },
            follow=True)
        self.assertRedirects(
            response,
            "/presupuestos/new/")
        self.assertContains(response, "Debe ingresar un monto")

        response = self.client.post(
            "/presupuestos/new/",
            data={
                "categoria": categoria.nombre,
                "monto": 10000
            },
            follow=True)
        self.assertRedirects(
            response,
            "/presupuestos/new/")
        self.assertEqual(Presupuesto.objects.count(), 0)
        self.assertContains(response, "Debe ingresar un período")

        response = self.client.post(
            "/presupuestos/new/",
            data={
                "year_month": this_period.id,
                "monto": 10000
            },
            follow=True)
        self.assertRedirects(
            response,
            "/presupuestos/new/")
        self.assertEqual(Presupuesto.objects.count(), 0)
        self.assertContains(response, "Debe ingresar una categoría")

    def test_user_can_create_new_presupuesto_for_current_period(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        categoria = Categoria.objects.all().first()
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)

        self.assertEqual(Presupuesto.objects.count(), 0)

        response = self.client.post(
            "/presupuestos/new/",
            data={
                "categoria": categoria.nombre,
                "year_month": this_period.id,
                "monto": 10000
            },
            follow=True)
        self.assertRedirects(
            response,
            "/presupuestos/%d/%d" % (this_period.year, this_period.month))
        self.assertEqual(Presupuesto.objects.count(), 1)
        self.assertEqual(
            Presupuesto.objects.all().first().categoria,
            categoria)
        self.assertEqual(
            Presupuesto.objects.all().first().monto,
            10000)
        self.assertEqual(
            Presupuesto.objects.all().first().year_month,
            this_period)
        self.assertContains(
            response,
            "El presupuesto fue creado exitósamente")

    def test_user_can_create_new_presupuesto_for_other_period(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        categoria = Categoria.objects.all().first()
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)
        other_year, other_month = this_period.get_next_period()
        other_period, __ = YearMonth.objects.get_or_create(
            year=other_year, month=other_month)

        self.assertEqual(Presupuesto.objects.count(), 0)

        response = self.client.post(
            "/presupuestos/new/",
            data={
                "categoria": categoria.nombre,
                "year_month": other_period.id,
                "monto": 10000
            },
            follow=True)
        self.assertRedirects(
            response,
            "/presupuestos/%d/%d" % (other_period.year, other_period.month))
        self.assertEqual(Presupuesto.objects.count(), 1)
        self.assertEqual(
            Presupuesto.objects.all().first().categoria,
            categoria)
        self.assertEqual(
            Presupuesto.objects.all().first().monto,
            10000)
        self.assertEqual(
            Presupuesto.objects.all().first().year_month,
            other_period)
        self.assertContains(
            response,
            "El presupuesto fue creado exitósamente")

    def test_user_cant_create_presupuesto_if_it_already_exists(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        categoria = Categoria.objects.all().first()
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)

        self.assertEqual(Presupuesto.objects.count(), 0)

        response = self.client.post(
            "/presupuestos/new/",
            data={
                "categoria": categoria.nombre,
                "year_month": this_period.id,
                "monto": 10000
            },
            follow=True)
        self.assertRedirects(
            response,
            "/presupuestos/%d/%d" % (this_period.year, this_period.month))
        self.assertEqual(Presupuesto.objects.count(), 1)
        self.assertEqual(
            Presupuesto.objects.all().first().categoria,
            categoria)
        self.assertEqual(
            Presupuesto.objects.all().first().monto,
            10000)
        self.assertEqual(
            Presupuesto.objects.all().first().year_month,
            this_period)

        # user tries to create it again
        response = self.client.post(
            "/presupuestos/new/",
            data={
                "categoria": categoria.nombre,
                "year_month": this_period.id,
                "monto": 20000
            },
            follow=True)
        self.assertRedirects(
            response,
            "/presupuestos/new/")
        self.assertEqual(Presupuesto.objects.count(), 1)
        self.assertEqual(
            Presupuesto.objects.all().first().categoria,
            categoria)
        self.assertEqual(
            Presupuesto.objects.all().first().monto,
            10000)
        self.assertEqual(
            Presupuesto.objects.all().first().year_month,
            this_period)
        self.assertContains(
            response,
            "Ya existe un presupuesto para el período seleccionado")


class EditPresupuestoTest(TestCase):

    # testing whether the user can see the form
    def test_not_logged_user_cant_see_presupuestos_edit_form(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        presupuesto = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=12345)
        url = "/presupuestos/%d/%d/%s/" % (
            presupuesto.year_month.year,
            presupuesto.year_month.month,
            presupuesto.categoria)

        self.client.logout()
        response = self.client.get(
            url,
            follow=True)

        self.assertRedirects(
            response,
            "/accounts/login/?next=%s" % (url))

    def test_homeless_user_cant_see_presupuestos_graph(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        presupuesto = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=12345)
        url = "/presupuestos/%d/%d/%s/" % (
            presupuesto.year_month.year,
            presupuesto.year_month.month,
            presupuesto.categoria)

        test_user.get_vu().leave()
        response = self.client.get(
            url,
            follow=True)

        self.assertRedirects(response, "/error/")
        self.assertNotContains(
            response,
            presupuesto.categoria)
        self.assertContains(
            response,
            "Para tener acceso a esta página debe pertenecer a una vivienda")

    def test_outsider_cant_see_presupuesto_of_vivienda(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        other_vivienda = Vivienda.objects.exclude(
            id=test_user.get_vivienda().id).first()
        my_presupuesto = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=12345)
        url = "/presupuestos/%d/%d/%s/" % (
            my_presupuesto.year_month.year,
            my_presupuesto.year_month.month,
            my_presupuesto.categoria)

        other_presupuesto = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=other_vivienda,
            monto=54321)
        response = self.client.get(
            url,
            follow=True)

        self.assertNotContains(response, other_presupuesto.monto)
        self.assertContains(response, my_presupuesto.monto)

    def test_past_user_cant_see_presupuesto_of_old_vivienda(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        presupuesto_old = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=12345)
        test_user.get_vu().leave()
        new_vivienda = Vivienda.objects.create(alias="my_new_viv")
        new_viv_usuario = ViviendaUsuario.objects.create(
            user=test_user, vivienda=new_vivienda)
        presupuesto_new = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=54321)
        url = "/presupuestos/%d/%d/%s/" % (
            presupuesto_old.year_month.year,
            presupuesto_old.year_month.month,
            presupuesto_old.categoria)
        response = self.client.get(
            url,
            follow=True)

        self.assertNotContains(response, presupuesto_old.monto)
        self.assertContains(response, presupuesto_new.monto)

    def test_non_existant_presupuesto_raises_404(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        presupuesto = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=12345)
        url = "/presupuestos/%d/%d/%s/" % (
            presupuesto.year_month.year + 1,
            presupuesto.year_month.month,
            presupuesto.categoria)
        response = self.client.get(
            url,
            follow=True)

        self.assertEqual(response.status_code, 404)

    def test_user_can_see_edit_presupuesto_form(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        presupuesto = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=12345)
        url = "/presupuestos/%d/%d/%s/" % (
            presupuesto.year_month.year,
            presupuesto.year_month.month,
            presupuesto.categoria)
        response = self.client.get(
            url,
            follow=True)

        self.assertContains(response, "<form")
        self.assertContains(response, "%d" % (presupuesto.monto))

    # testing whether the user make a post request to modify the presupuesto
    def test_not_logged_user_cant_edit_presupuestos(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        presupuesto = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=100)
        url = "/presupuestos/%d/%d/%s/" % (
            presupuesto.year_month.year,
            presupuesto.year_month.month,
            presupuesto.categoria)

        self.client.logout()
        response = self.client.post(
            url,
            data={
                "monto": 200
            },
            follow=True)

        self.assertRedirects(
            response,
            "/accounts/login/?next=%s" % (url))
        self.assertNotEqual(
            Presupuesto.objects.get(id=presupuesto.id).monto,
            200)
        self.assertNotEqual(
            Presupuesto.objects.get(id=presupuesto.id).monto,
            300)
        self.assertEqual(
            Presupuesto.objects.get(id=presupuesto.id).monto,
            100)

    def test_homeless_user_cant_edit_presupuesto(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        presupuesto = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=100)
        url = "/presupuestos/%d/%d/%s/" % (
            presupuesto.year_month.year,
            presupuesto.year_month.month,
            presupuesto.categoria)

        test_user.get_vu().leave()
        response = self.client.post(
            url,
            data={
                "monto": 200
            },
            follow=True)

        self.assertRedirects(response, "/error/")
        self.assertNotContains(
            response,
            presupuesto.categoria)
        self.assertContains(
            response,
            "Para tener acceso a esta página debe pertenecer a una vivienda")
        self.assertNotEqual(
            Presupuesto.objects.get(id=presupuesto.id).monto,
            200)
        self.assertNotEqual(
            Presupuesto.objects.get(id=presupuesto.id).monto,
            300)
        self.assertEqual(
            Presupuesto.objects.get(id=presupuesto.id).monto,
            100)

    def test_outsider_cant_edit_presupuesto_of_vivienda(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        other_vivienda = Vivienda.objects.exclude(
            id=test_user.get_vivienda().id).first()
        other_presupuesto = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=other_vivienda,
            monto=300)

        url = "/presupuestos/%d/%d/%s/" % (
            other_presupuesto.year_month.year,
            other_presupuesto.year_month.month,
            other_presupuesto.categoria)
        response = self.client.post(
            url,
            data={
                "monto": 200
            },
            follow=True)
        self.assertEqual(response.status_code, 404)
        self.assertNotEqual(
            Presupuesto.objects.get(id=other_presupuesto.id).monto,
            200)
        self.assertEqual(
            Presupuesto.objects.get(id=other_presupuesto.id).monto,
            300)

    def test_past_user_cant_edit_presupuesto_of_old_vivienda(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        presupuesto_old = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=300)
        test_user.get_vu().leave()
        new_vivienda = Vivienda.objects.create(alias="my_new_viv")
        new_viv_usuario = ViviendaUsuario.objects.create(
            user=test_user, vivienda=new_vivienda)

        url = "/presupuestos/%d/%d/%s/" % (
            presupuesto_old.year_month.year,
            presupuesto_old.year_month.month,
            presupuesto_old.categoria)
        response = self.client.post(
            url,
            data={
                "monto": 200
            },
            follow=True)

        self.assertEqual(response.status_code, 404)
        self.assertNotEqual(
            Presupuesto.objects.get(id=presupuesto_old.id).monto,
            200)
        self.assertEqual(
            Presupuesto.objects.get(id=presupuesto_old.id).monto,
            300)

    def test_posting_to_non_existant_presupuesto_raises_404(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        presupuesto = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=300)
        next_year, next_month = presupuesto.year_month.get_next_period()

        url = "/presupuestos/%d/%d/%s/" % (
            next_year,
            next_month,
            presupuesto.categoria)
        response = self.client.post(
            url,
            data={
                "monto": 200
            },
            follow=True)

        self.assertEqual(response.status_code, 404)
        self.assertNotEqual(
            Presupuesto.objects.get(id=presupuesto.id).monto,
            200)
        self.assertEqual(
            Presupuesto.objects.get(id=presupuesto.id).monto,
            300)

    def test_user_cant_edit_presupuesto_with_broken_POST(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        presupuesto = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=300)
        url = "/presupuestos/%d/%d/%s/" % (
            presupuesto.year_month.year,
            presupuesto.year_month.month,
            presupuesto.categoria)

        response = self.client.post(
            url,
            data={
                "asdf": "asdf"
            },
            follow=True)

        self.assertRedirects(response, url)
        self.assertContains(response, "Debe ingresar un monto")
        self.assertEqual(
            Presupuesto.objects.get(id=presupuesto.id).monto,
            300)

        response = self.client.post(
            url,
            data={
                "monto": ""
            },
            follow=True)

        self.assertRedirects(response, url)
        self.assertContains(response, "Debe ingresar un monto mayor a 0")
        self.assertEqual(
            Presupuesto.objects.get(id=presupuesto.id).monto,
            300)

        response = self.client.post(
            url,
            data={
                "monto": 0
            },
            follow=True)

        self.assertRedirects(response, url)
        self.assertContains(response, "Debe ingresar un monto mayor a 0")
        self.assertEqual(
            Presupuesto.objects.get(id=presupuesto.id).monto,
            300)

    def test_user_can_edit_presupuesto(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        presupuesto = Presupuesto.objects.create(
            categoria=Categoria.objects.all().first(),
            vivienda=test_user.get_vivienda(),
            monto=100)
        url = "/presupuestos/%d/%d/%s/" % (
            presupuesto.year_month.year,
            presupuesto.year_month.month,
            presupuesto.categoria)

        self.assertEqual(Presupuesto.objects.count(), 1)

        response = self.client.post(
            url,
            data={
                "monto": 200
            },
            follow=True)

        self.assertRedirects(
            response,
            "/graphs/presupuestos/%d/%d" % (
                presupuesto.year_month.year,
                presupuesto.year_month.month))
        self.assertContains(response, "Presupuesto modificado con éxito")
        self.assertEqual(Presupuesto.objects.count(), 1)
        self.assertNotEqual(
            Presupuesto.objects.get(id=presupuesto.id).monto,
            100)
        self.assertEqual(
            Presupuesto.objects.get(id=presupuesto.id).monto,
            200)
