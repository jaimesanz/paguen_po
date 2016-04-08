from django.core.urlresolvers import resolve, reverse
from django.test import TestCase
from django.http import HttpRequest
from django.template.loader import render_to_string
from expenses_manager.models import *

class ProxyUserModelTest(TestCase):
	
	def test_user_ha_no_vivienda(self):
		user1 = ProxyUser.objects.create(username="us1", email="a@a.com")
		correct_vivienda = Vivienda.objects.create(alias="viv1")

		# user has no vivienda
		self.assertFalse(user1.has_vivienda())
		self.assertEqual(user1.get_vivienda(), None)
		self.assertEqual(user1.get_vu(), None)
		self.assertEqual(user1.get_roommates().count(), 0)

	def test_user_joins_vivienda(self):
		user1 = ProxyUser.objects.create(username="us1", email="a@a.com")
		correct_vivienda = Vivienda.objects.create(alias="viv1")

		# user joins a vivienda
		user1_viv = ViviendaUsuario.objects.create(vivienda=correct_vivienda , user=user1)
		self.assertTrue(user1.has_vivienda())
		self.assertEqual(user1.get_vivienda().alias, "viv1")
		self.assertNotEqual(user1.get_vivienda().alias, "viv2")
		self.assertTrue(user1.get_roommates().count(), 1)
		self.assertIn(user1.get_vu(), user1.get_roommates())
		self.assertEqual(user1.get_vu(), user1_viv)

	def test_another_user_joins_vivienda(self):
		user1 = ProxyUser.objects.create(username="us1", email="a@a.com")
		user2 = ProxyUser.objects.create(username="us2", email="b@b.com")
		correct_vivienda = Vivienda.objects.create(alias="viv1")

		# user joins a vivienda, and then another user also joins
		user1_viv = ViviendaUsuario.objects.create(vivienda=correct_vivienda , user=user1)
		user2_viv = ViviendaUsuario.objects.create(vivienda=correct_vivienda , user=user2)

		self.assertEqual(user2.get_vivienda().alias, "viv1")
		self.assertNotEqual(user2.get_vivienda().alias, "viv2")
		self.assertEqual(user2.get_roommates().count(), 2)
		self.assertEqual(user1.get_roommates().count(), user2.get_roommates().count())
		self.assertIn(user2.get_vu(), user2.get_roommates())
		self.assertIn(user1.get_vu(), user2.get_roommates())
		self.assertIn(user2.get_vu(), user1.get_roommates())
		self.assertIn(user1.get_vu(), user1.get_roommates())

	def test_user_leaves_vivienda_and_leaves_roommate_alone(self):
		user1 = ProxyUser.objects.create(username="us1", email="a@a.com")
		user2 = ProxyUser.objects.create(username="us2", email="b@b.com")
		correct_vivienda = Vivienda.objects.create(alias="viv1")
		user1_viv = ViviendaUsuario.objects.create(vivienda=correct_vivienda , user=user1)
		user2_viv = ViviendaUsuario.objects.create(vivienda=correct_vivienda , user=user2)

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
		user1 = ProxyUser.objects.create(username="us1", email="a@a.com")
		user2 = ProxyUser.objects.create(username="us2", email="b@b.com")
		correct_vivienda = Vivienda.objects.create(alias="viv1")
		other_vivienda = Vivienda.objects.create(alias="viv2")
		user1_viv = ViviendaUsuario.objects.create(vivienda=correct_vivienda , user=user1)
		user2_viv = ViviendaUsuario.objects.create(vivienda=correct_vivienda , user=user2)

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
		user1 = ProxyUser.objects.create(username="us1", email="a@a.com")

		# user has no invites
		invites_in, invites_out = user1.get_invites()
		self.assertEqual(invites_in.count(), 0)
		self.assertEqual(invites_out.count(), 0)

	def test_user_invites_another(self):
		user1 = ProxyUser.objects.create(username="us1", email="a@a.com")
		user2 = ProxyUser.objects.create(username="us2", email="b@b.com")
		correct_vivienda = Vivienda.objects.create(alias="viv1")
		user1_viv = ViviendaUsuario.objects.create(vivienda=correct_vivienda , user=user1)

		Invitacion.objects.create(invitado=user2, invitado_por=user1_viv, email="b@b.com")
		self.assertEqual(user2.get_invites()[0].count(), 1)
		self.assertEqual(user1.get_invites()[1].count(), 1)

	def test_user_accepts_invite(self):
		user1 = ProxyUser.objects.create(username="us1", email="a@a.com")
		user2 = ProxyUser.objects.create(username="us2", email="b@b.com")
		correct_vivienda = Vivienda.objects.create(alias="viv1")
		user1_viv = ViviendaUsuario.objects.create(vivienda=correct_vivienda , user=user1)

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
		user1 = ProxyUser.objects.create(username="us1", email="a@a.com")
		user2 = ProxyUser.objects.create(username="us2", email="b@b.com")
		correct_vivienda = Vivienda.objects.create(alias="viv1")
		user1_viv = ViviendaUsuario.objects.create(vivienda=correct_vivienda , user=user1)

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
		user1 = ProxyUser.objects.create(username="us1", email="a@a.com")
		user2 = ProxyUser.objects.create(username="us2", email="b@b.com")
		correct_vivienda = Vivienda.objects.create(alias="viv1")
		user1_viv = ViviendaUsuario.objects.create(vivienda=correct_vivienda , user=user1)
		user2_viv = ViviendaUsuario.objects.create(vivienda=correct_vivienda , user=user2)

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
		user1 = ProxyUser.objects.create(username="us1", email="a@a.com")
		correct_vivienda = Vivienda.objects.create(alias="viv1")
		user1_viv = ViviendaUsuario.objects.create(vivienda=correct_vivienda , user=user1)
		dummy_categoria = Categoria.objects.create(nombre="dummy")
		gasto = Gasto.objects.create(
			monto=1000,
			creado_por=user1_viv,
			categoria=dummy_categoria)

		self.assertFalse(gasto.is_paid())
		self.assertTrue(gasto.is_pending())
		self.assertTrue(gasto.allow_user(user1))
		user1.pagar(gasto)
		self.assertFalse(gasto.is_pending())
		self.assertTrue(gasto.is_paid())
		self.assertTrue(gasto.allow_user(user1))

class ViviendaModelTest(TestCase):
	def test_pass(self):
		pass

class ViviendaUsuarioModelTest(TestCase):
	def test_pass(self):
		pass

class InvitacionModelTest(TestCase):
	def test_pass(self):
		pass

class SolicitudAbandonarViviendaModelTest(TestCase):
	def test_pass(self):
		pass

class CategoriaModelTest(TestCase):
	def test_pass(self):
		pass

class ItemModelTest(TestCase):
	def test_pass(self):
		pass

class YearMonthModelTest(TestCase):
	def test_pass(self):
		pass

class PresupuestoModelTest(TestCase):
	def test_pass(self):
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
