from django.core.urlresolvers import resolve, reverse
from django.test import TestCase
from django.http import HttpRequest
from django.template.loader import render_to_string
from expenses_manager.models import *

def get_lone_user():
	return ProxyUser.objects.create(username="us1", email="a@a.com")

def get_vivienda_with_1_user():
	user1 = get_lone_user()
	correct_vivienda = Vivienda.objects.create(alias="viv1")
	user1_viv = ViviendaUsuario.objects.create(vivienda=correct_vivienda , user=user1)
	return (user1, correct_vivienda, user1_viv)

def get_vivienda_with_2_users():
	user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
	user2 = ProxyUser.objects.create(username="us2", email="b@b.com")
	user2_viv = ViviendaUsuario.objects.create(vivienda=correct_vivienda , user=user2)
	return (user1, user2, correct_vivienda, user1_viv, user2_viv)

def get_dummy_gasto_pendiente(user_viv):
	dummy_categoria = Categoria.objects.create(nombre="dummy")
	gasto = Gasto.objects.create(
		monto=1000,
		creado_por=user_viv,
		categoria=dummy_categoria)
	return gasto, dummy_categoria


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
		user1, user2, correct_vivienda, user1_viv, user2_viv = get_vivienda_with_2_users()

		self.assertEqual(user2.get_vivienda().alias, "viv1")
		self.assertNotEqual(user2.get_vivienda().alias, "viv2")
		self.assertEqual(user2.get_roommates().count(), 2)
		self.assertEqual(user1.get_roommates().count(), user2.get_roommates().count())
		self.assertIn(user2.get_vu(), user2.get_roommates())
		self.assertIn(user1.get_vu(), user2.get_roommates())
		self.assertIn(user2.get_vu(), user1.get_roommates())
		self.assertIn(user1.get_vu(), user1.get_roommates())

	def test_user_leaves_vivienda_and_leaves_roommate_alone(self):
		user1, user2, correct_vivienda, user1_viv, user2_viv = get_vivienda_with_2_users()

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
		self.assertNotEqual(user1.get_roommates().count(), user2.get_roommates().count())

	def test_user_leaves_vivienda_and_joins_a_new_one(self):
		user1, user2, correct_vivienda, user1_viv, user2_viv = get_vivienda_with_2_users()
		other_vivienda = Vivienda.objects.create(alias="viv2")

		# first user leaves and joins another 
		user1_viv.estado = "inactivo"
		user1_viv.save()
		user1_new_viv = ViviendaUsuario.objects.create(vivienda=other_vivienda, user=user1)

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

		Invitacion.objects.create(invitado=user2, invitado_por=user1_viv, email="b@b.com")
		self.assertEqual(user2.get_invites()[0].count(), 1)
		self.assertEqual(user1.get_invites()[1].count(), 1)

	def test_user_accepts_invite(self):
		user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
		user2 = ProxyUser.objects.create(username="us2", email="b@b.com")

		invite = Invitacion.objects.create(invitado=user2, invitado_por=user1_viv, email="b@b.com")
		invite.accept()

		self.assertEqual(user2.get_invites()[0].count(), 0)
		self.assertEqual(user1.get_invites()[1].count(), 0)

		# user2 joined the vivienda
		self.assertEqual(user2.get_vivienda().alias, "viv1")
		self.assertNotEqual(user2.get_vivienda().alias, "viv2")
		self.assertEqual(user2.get_roommates().count(), 2)
		self.assertEqual(user1.get_roommates().count(), user2.get_roommates().count())
		self.assertIn(user2.get_vu(), user2.get_roommates())
		self.assertIn(user1.get_vu(), user2.get_roommates())
		self.assertIn(user2.get_vu(), user1.get_roommates())
		self.assertIn(user1.get_vu(), user1.get_roommates())

	def test_user_rejects_invite(self):
		user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
		user2 = ProxyUser.objects.create(username="us2", email="b@b.com")

		invite = Invitacion.objects.create(invitado=user2, invitado_por=user1_viv, email="b@b.com")
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
		user1, user2, correct_vivienda, user1_viv, user2_viv = get_vivienda_with_2_users()

		# first user leaves and returns
		user1_viv.estado = "inactivo"
		user1_viv.save()
		ViviendaUsuario.objects.create(vivienda=correct_vivienda, user=user1)

		# both users are in the vivienda
		self.assertEqual(user2.get_vivienda().alias, "viv1")
		self.assertEqual(user2.get_roommates().count(), 2)
		self.assertEqual(user1.get_roommates().count(), user2.get_roommates().count())
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
		user1 = ProxyUser.objects.create(username="us1", email="a@a.com")
		correct_vivienda = Vivienda.objects.create(alias="viv1")
		user1_viv = ViviendaUsuario.objects.create(vivienda=correct_vivienda , user=user1)

		gastos_pendientes_direct = correct_vivienda.get_gastos_pendientes()
		gastos_pagados_direct = correct_vivienda.get_gastos_pagados()
		gastos_pendientes, gastos_pagados = correct_vivienda.get_gastos()

		self.assertEqual(gastos_pendientes.count(), 0)
		self.assertEqual(gastos_pagados.count(), 0)
		self.assertEqual(gastos_pendientes_direct.count(), 0)
		self.assertEqual(gastos_pagados_direct.count(), 0)

	def test_get_gastos_from_vivienda_with_gastos_pendientes(self):
		user1 = ProxyUser.objects.create(username="us1", email="a@a.com")
		correct_vivienda = Vivienda.objects.create(alias="viv1")
		user1_viv = ViviendaUsuario.objects.create(vivienda=correct_vivienda , user=user1)
		dummy_categoria = Categoria.objects.create(nombre="dummy")
		gasto = Gasto.objects.create(
			monto=1000,
			creado_por=user1_viv,
			categoria=dummy_categoria)

		gastos_pendientes_direct = correct_vivienda.get_gastos_pendientes()
		gastos_pagados_direct = correct_vivienda.get_gastos_pagados()
		gastos_pendientes, gastos_pagados = correct_vivienda.get_gastos()

		self.assertEqual(gastos_pendientes.count(), 1)
		self.assertEqual(gastos_pagados.count(), 0)
		self.assertEqual(gastos_pendientes_direct.count(), 1)
		self.assertEqual(gastos_pagados_direct.count(), 0)

	def test_get_gastos_from_vivienda_with_gastos_pagados(self):
		user1 = ProxyUser.objects.create(username="us1", email="a@a.com")
		correct_vivienda = Vivienda.objects.create(alias="viv1")
		user1_viv = ViviendaUsuario.objects.create(vivienda=correct_vivienda , user=user1)
		dummy_categoria = Categoria.objects.create(nombre="dummy")
		gasto = Gasto.objects.create(
			monto=1000,
			creado_por=user1_viv,
			categoria=dummy_categoria)
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

		user1_viv.leave()

		self.assertFalse(user1.has_vivienda())
		self.assertFalse(user1_viv.is_active())

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

	def test_user_gets_gastos_of_vivienda_that_has_gastos_pendientes_and_pays_them(self):
		user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
		gasto, dummy_categoria = get_dummy_gasto_pendiente(user1_viv)
		user1_viv.pagar(gasto)

		gastos_pendientes, gastos_pagados = user1_viv.get_gastos_vivienda()

		self.assertEqual(gastos_pendientes.count(), 0)
		self.assertEqual(gastos_pagados.count(), 1)

class InvitacionModelTest(TestCase):
	def test_pass(self):
		pass

class SolicitudAbandonarViviendaModelTest(TestCase):
	pass

class CategoriaModelTest(TestCase):
	pass

class ItemModelTest(TestCase):
	pass

class YearMonthModelTest(TestCase):
	pass

class PresupuestoModelTest(TestCase):
	pass

class ListaComprasModelTest(TestCase):
	def test_pass(self):
		pass

class ItemListaModelTest(TestCase):
	def test_pass(self):
		pass

class EstadoGastoModelTest(TestCase):
	def test_pass(self):
		pass

class GastoModelTest(TestCase):
	def test_pass(self):
		pass
