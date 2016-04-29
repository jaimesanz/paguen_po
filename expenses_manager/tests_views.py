from django.core.urlresolvers import resolve, reverse
from django.test import TestCase
from django.http import HttpRequest
from django.template.loader import render_to_string
from expenses_manager.models import *
from django.utils import timezone
from expenses_manager.views import *
from .helper_functions_tests import *


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
            data={
                "categoria": dummy_categoria.id,
                "monto": 232
            },
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
            data={
                "categoria": dummy_categoria.id,
                "monto": 232,
                "is_paid": "no"
            },
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
            data={
                "categoria": dummy_categoria.id,
                "monto": 232,
                "is_paid": "yes"
            },
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
        self.assertEqual(Item.objects.filter(vivienda=vivienda).count(), 3)

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
        vivienda = test_user.get_vivienda()
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)
        next_year, next_month = this_period.get_next_period()
        next_period, __ = YearMonth.objects.get_or_create(
            year=next_year, month=next_month)
        presupuesto_cat1 = Presupuesto.objects.create(
            categoria=Categoria.objects.create(
                nombre="d1",
                vivienda=vivienda),
            vivienda=vivienda,
            year_month=this_period,
            monto=12345)

        presupuesto_cat2 = Presupuesto.objects.create(
            categoria=Categoria.objects.create(
                nombre="d2",
                vivienda=vivienda),
            vivienda=vivienda,
            year_month=this_period,
            monto=54321)
        response = self.client.get(
            "/presupuestos/",
            follow=True)

        self.assertContains(response, presupuesto_cat1.categoria)
        self.assertContains(response, presupuesto_cat2.categoria)


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
        cat = Categoria.objects.create(
            nombre="dumdum",
            vivienda=test_user.get_vivienda())
        presupuesto = Presupuesto.objects.create(
            categoria=cat,
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
        cat = Categoria.objects.create(
            nombre="dumdum",
            vivienda=test_user.get_vivienda())
        presupuesto = Presupuesto.objects.create(
            categoria=cat,
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
        cat = Categoria.objects.create(
            nombre="dumdum",
            vivienda=test_user.get_vivienda())
        other_presupuesto = Presupuesto.objects.create(
            categoria=cat,
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
        cat = Categoria.objects.create(
            nombre="dumdum",
            vivienda=test_user.get_vivienda())
        presupuesto_new = Presupuesto.objects.create(
            categoria=cat,
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
        cat = Categoria.objects.create(
            nombre="dumdum",
            vivienda=test_user.get_vivienda())
        presupuesto_now = Presupuesto.objects.create(
            categoria=cat,
            vivienda=test_user.get_vivienda(),
            year_month=this_period,
            monto=12345)

        presupuesto_next = Presupuesto.objects.create(
            categoria=cat,
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
        cat = Categoria.objects.create(
            nombre="dumdum",
            vivienda=test_user.get_vivienda())
        presupuesto_now = Presupuesto.objects.create(
            categoria=cat,
            vivienda=test_user.get_vivienda(),
            year_month=this_period,
            monto=12345)

        presupuesto_next = Presupuesto.objects.create(
            categoria=cat,
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
        cat = Categoria.objects.create(
            nombre="dumdum",
            vivienda=test_user.get_vivienda())
        presupuesto_now = Presupuesto.objects.create(
            categoria=cat,
            vivienda=test_user.get_vivienda(),
            year_month=this_period,
            monto=12345)

        presupuesto_prev = Presupuesto.objects.create(
            categoria=cat,
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
        cat = Categoria.objects.create(
            nombre="dumdum",
            vivienda=test_user.get_vivienda())
        presupuesto_now = Presupuesto.objects.create(
            categoria=cat,
            vivienda=test_user.get_vivienda(),
            year_month=this_period,
            monto=12345)

        presupuesto_next = Presupuesto.objects.create(
            categoria=cat,
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
        cat = Categoria.objects.create(
            nombre="dumdum",
            vivienda=test_user.get_vivienda())
        presupuesto_now = Presupuesto.objects.create(
            categoria=cat,
            vivienda=test_user.get_vivienda(),
            year_month=this_period,
            monto=12345)

        presupuesto_next = Presupuesto.objects.create(
            categoria=cat,
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
        vivienda = test_user.get_vivienda()
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)
        next_year, next_month = this_period.get_next_period()
        next_period, __ = YearMonth.objects.get_or_create(
            year=next_year, month=next_month)
        presupuesto_cat1 = Presupuesto.objects.create(
            categoria=Categoria.objects.create(
                nombre="d1",
                vivienda=vivienda),
            vivienda=vivienda,
            year_month=this_period,
            monto=12345)

        presupuesto_cat2 = Presupuesto.objects.create(
            categoria=Categoria.objects.create(
                nombre="d2",
                vivienda=vivienda),
            vivienda=vivienda,
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
                "categoria": categoria.id,
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
                "categoria": categoria.id,
                "year_month": this_period.id,
                "monto": 10000
            },
            follow=True)
        self.assertRedirects(
            response,
            "/error/")
        self.assertContains(
            response,
            "Para tener acceso a esta página debe pertenecer a una vivienda")

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
                "categoria": categoria.id,
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
                "categoria": categoria.id,
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
        categoria = Categoria.objects.create(
            nombre="dumdum",
            vivienda=test_user.get_vivienda())
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)

        self.assertEqual(Presupuesto.objects.count(), 0)

        response = self.client.post(
            "/presupuestos/new/",
            data={
                "categoria": categoria.id,
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
        categoria = Categoria.objects.create(
            nombre="dumdum",
            vivienda=test_user.get_vivienda())
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
                "categoria": categoria.id,
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
        categoria = Categoria.objects.create(
            nombre="dumdum",
            vivienda=test_user.get_vivienda())
        now = timezone.now()
        this_period, __ = YearMonth.objects.get_or_create(
            year=now.year, month=now.month)

        self.assertEqual(Presupuesto.objects.count(), 0)

        response = self.client.post(
            "/presupuestos/new/",
            data={
                "categoria": categoria.id,
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
                "categoria": categoria.id,
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
        vivienda = test_user.get_vivienda()
        cat_old = Categoria.objects.create(
            nombre="common_name",
            vivienda=vivienda)
        presupuesto_old = Presupuesto.objects.create(
            categoria=cat_old,
            vivienda=vivienda,
            monto=12345)
        test_user.get_vu().leave()
        new_vivienda = Vivienda.objects.create(alias="my_new_viv")
        new_viv_usuario = ViviendaUsuario.objects.create(
            user=test_user, vivienda=new_vivienda)
        cat_new = Categoria.objects.create(
            nombre="common_name",
            vivienda=new_vivienda)
        presupuesto_new = Presupuesto.objects.create(
            categoria=cat_new,
            vivienda=new_vivienda,
            monto=54321)
        url = "/presupuestos/%d/%d/%s/" % (
            presupuesto_old.year_month.year,
            presupuesto_old.year_month.month,
            presupuesto_old.categoria)
        response = self.client.get(
            url,
            follow=True)

        self.assertNotContains(
            response,
            presupuesto_old.monto)
        self.assertContains(
            response,
            presupuesto_new.monto)

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


class BalanceViewTest(TestCase):

    url = "/vivienda/balance/"

    def test_not_logged_user_cant_see_balance(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        self.client.logout()
        response = self.client.get(
            self.url,
            follow=True)

        self.assertRedirects(
            response,
            "/accounts/login/?next=%s" % (self.url))

    def test_homeless_user_cant_see_balance(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        test_user.get_vu().leave()
        response = self.client.get(
            self.url,
            follow=True)

        self.assertRedirects(
            response,
            "/error/")
        self.assertContains(
            response,
            "Para tener acceso a esta página debe pertenecer a una vivienda")

    def test_user_can_see_roommates(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        response = self.client.get(
            self.url,
            follow=True)

        for roommate in test_user.get_roommates():
            self.assertContains(
                response,
                roommate.user)

    def test_user_can_see_total_expenses(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(self)

        test_user_1.pagar(gasto_1)
        test_user_1.pagar(gasto_2)

        response = self.client.get(
            self.url,
            follow=True)

        self.assertContains(response, gasto_1.monto + gasto_2.monto)
        self.assertContains(response, 0)

    def test_user_can_see_total_expenses_of_roommates(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(self)

        test_user_1.pagar(gasto_1)
        test_user_2.pagar(gasto_2)

        response = self.client.get(
            self.url,
            follow=True)

        self.assertContains(response, gasto_1.monto)
        self.assertContains(response, gasto_2.monto)


class CategoriaListViewTest(TestCase):

    url = "/vivienda/categorias/"
    url_new = "/vivienda/categorias/new/"

    # not logged cant see
    def test_not_logged_user_cant_see_categorias(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        self.client.logout()
        response = self.client.get(
            self.url,
            follow=True)

        self.assertRedirects(
            response,
            "/accounts/login/?next=%s" % (self.url))
    # homeless cant see

    def test_homeless_user_cant_see_categorias(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        test_user.get_vu().leave()
        response = self.client.get(
            self.url,
            follow=True)

        self.assertRedirects(
            response,
            "/error/")
        self.assertContains(
            response,
            "Para tener acceso a esta página debe pertenecer a una vivienda")
    # user can only see categorias of his vivienda

    def test_user_can_see_categorias_of_active_vivienda_only(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(self)
        categoria_1 = Categoria.objects.create(
            vivienda=test_user_1.get_vivienda(),
            nombre="custom_1")
        categoria_2 = Categoria.objects.create(
            vivienda=test_user_3.get_vivienda(),
            nombre="custom_2")

        response = self.client.get(
            self.url,
            follow=True)

        self.assertContains(response, categoria_1)
        self.assertNotContains(response, categoria_2)
        self.assertContains(response, dummy_categoria)

    # user can create new categoria
    def test_user_can_create_custom_categoria(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        categoria_count = Categoria.objects.count()
        response = self.client.post(
            self.url_new,
            data={
                "nombre": "custom_1"
            },
            follow=True)

        self.assertRedirects(response, self.url)
        self.assertContains(response, "¡Categoría agregada!")
        self.assertEqual(
            categoria_count,
            Categoria.objects.count() - 1)

    # user cant create categoria with broken post
    def test_user_cant_create_custom_categoria_w_broken_POST(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        categoria_count = Categoria.objects.count()

        response = self.client.post(
            self.url_new,
            data={
                "nombre": ""
            },
            follow=True)

        self.assertRedirects(response, self.url_new)
        self.assertContains(response, "Debe ingresar un nombre de categoría")
        self.assertEqual(categoria_count, Categoria.objects.count())

        response = self.client.post(
            self.url_new,
            data={
                "weird_key": "SQLInj",
                "not_name_key": "some_rubbish"
            },
            follow=True)

        self.assertRedirects(response, self.url_new)
        self.assertContains(response, "Debe ingresar un nombre de categoría")
        self.assertEqual(categoria_count, Categoria.objects.count())

    # user CANT create custom categoria that already exists as global
    def test_user_cant_create_custom_categoria_that_exists_as_global(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        categoria_count = Categoria.objects.count()

        response = self.client.post(
            self.url_new,
            data={
                "nombre": "dummy1"
            },
            follow=True)

        self.assertRedirects(response, self.url_new)
        self.assertContains(
            response,
            "El nombre ingresado corresponde a una categoría global")
        self.assertEqual(categoria_count, Categoria.objects.count())

    # user CAN create custom categoria even if another vivienda has the same
    # custom categoria
    def test_user_can_create_cstm_categoria_that_exists_for_other_viv(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(self)
        custom_categoria = Categoria.objects.create(
            vivienda=test_user_3.get_vivienda(),
            nombre="custom_1")
        categoria_count = Categoria.objects.count()

        response = self.client.post(
            self.url_new,
            data={
                "nombre": "custom_1"
            },
            follow=True)

        self.assertRedirects(response, self.url)
        self.assertContains(response, "¡Categoría agregada!")
        self.assertEqual(
            categoria_count,
            Categoria.objects.count() - 1)

    def test_user_can_hide_categoria(self):
        """
        If a user HIDES a categoria, it won't show when the vivienda gets
        the list of Categorias, but Gastos of a hidden Categoria
        still count towards the common purse. These Gastos' Categoria will
        be shown as the default "other" Categoria -> "Otros"
        """
        # create users and viviendas
        (test_user_1,
            __,
            __,
            dummy_categoria,
            gasto_1,
            gasto_2,
            __) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(self)
        vivienda = test_user_1.get_vivienda()
        gasto_1.pagar(test_user_1)
        gasto_2.pagar(test_user_1)
        otros_cat = Categoria.objects.create(
            nombre="Otros",
            vivienda=vivienda)
        total_dummy = vivienda.get_total_expenses_categoria_period(
            categoria=dummy_categoria,
            year_month=gasto_1.year_month)
        total_otros = vivienda.get_total_expenses_categoria_period(
            categoria=otros_cat,
            year_month=gasto_1.year_month)
        # check that categoria is not hidden (database)
        self.assertFalse(dummy_categoria.is_hidden())
        self.assertEqual(total_otros, 0)
        self.assertEqual(total_dummy, gasto_1.monto + gasto_2.monto)
        # user send POST to hide categoria
        response = self.client.post(
            self.url,
            data={
                "categoria": "dummy1"
            },
            follow=True)
        # user is redirected to same page
        self.assertRedirects(response, self.url)
        # check that categoria is hidden (database)
        dummy_categoria = Categoria.objects.get(id=dummy_categoria.id)
        self.assertTrue(dummy_categoria.is_hidden())
        # get total of "Otros" Gastos, and check that it's the same as the
        # sum of hidden gastos
        total_dummy = vivienda.get_total_expenses_categoria_period(
            categoria=dummy_categoria,
            year_month=gasto_1.year_month)
        total_otros = vivienda.get_total_expenses_categoria_period(
            categoria=otros_cat,
            year_month=gasto_1.year_month)
        self.assertEqual(total_dummy, 0)
        self.assertEqual(total_otros, gasto_1.monto + gasto_2.monto)

    def test_user_can_unhide_categoria(self):
        """
        if a user UN-HIDES a categoria, it will show when the vivienda gets
        the list of categorias
        """
        (test_user_1,
            __,
            __,
            dummy_categoria,
            gasto_1,
            gasto_2,
            __) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(self)
        gasto_1.pagar(test_user_1)
        gasto_2.pagar(test_user_1)
        vivienda = test_user_1.get_vivienda()
        # hide categoria
        dummy_categoria.hide()
        otros_cat = Categoria.objects.create(
            nombre="Otros",
            vivienda=vivienda)
        # get total expenses
        total_dummy = vivienda.get_total_expenses_categoria_period(
            categoria=dummy_categoria,
            year_month=gasto_1.year_month)
        total_otros = vivienda.get_total_expenses_categoria_period(
            categoria=otros_cat,
            year_month=gasto_1.year_month)
        # check that categoria is hidden (database)
        self.assertTrue(dummy_categoria.is_hidden())
        # user send POST to un-hide categoria
        response = self.client.post(
            self.url,
            data={
                "categoria": "dummy1"
            },
            follow=True)
        # user is redirected to same page
        self.assertRedirects(response, self.url)
        # check that categoria is not hidden (database)
        dummy_categoria = Categoria.objects.get(id=dummy_categoria.id)
        self.assertFalse(dummy_categoria.is_hidden())
        total_dummy = vivienda.get_total_expenses_categoria_period(
            categoria=dummy_categoria,
            year_month=gasto_1.year_month)
        total_otros = vivienda.get_total_expenses_categoria_period(
            categoria=otros_cat,
            year_month=gasto_1.year_month)
        self.assertEqual(total_dummy, gasto_1.monto + gasto_2.monto)
        self.assertEqual(total_otros, 0)

    def test_user_can_delete_categoria_and_transfer_gastos_to_otros(self):
        """
        If a user DELETES a custom categoria, all gastos of this categoria
        are transfered to the default "otros" categoria
        """
        (test_user_1,
            __,
            __,
            __,
            __,
            __,
            __) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(self)
        vivienda = test_user_1.get_vivienda()
        custom_categoria = Categoria.objects.create(
            nombre="dumdum",
            vivienda=vivienda)
        otros_cat = Categoria.objects.create(
            nombre="Otros",
            vivienda=vivienda)
        gasto_custom_cat = Gasto.objects.create(
            monto=1000,
            creado_por=test_user_1.get_vu(),
            categoria=custom_categoria)
        self.assertEqual(
            Gasto.objects.filter(categoria=custom_categoria).count(),
            1)
        self.assertEqual(
            Gasto.objects.filter(categoria=otros_cat).count(),
            0)

        response = self.client.post(
            "/vivienda/categorias/delete/",
            data={
                "categoria": custom_categoria.id
            },
            follow=True)

        self.assertRedirects(response, self.url)
        self.assertFalse(Categoria.objects.filter(
            id=custom_categoria.id).exists())
        self.assertFalse(Categoria.objects.filter(
            nombre=custom_categoria.nombre,
            vivienda=vivienda).exists())
        self.assertEqual(
            Gasto.objects.filter(categoria=custom_categoria).count(),
            0)
        self.assertEqual(
            Gasto.objects.filter(categoria=otros_cat).count(),
            1)

    def test_user_cant_delete_global_categoria(self):
        (test_user_1,
            __,
            __,
            __,
            __,
            __,
            __) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(self)
        vivienda = test_user_1.get_vivienda()
        global_categoria = Categoria.objects.create(
            nombre="global_cat")
        categoria = Categoria.objects.create(
            nombre="global_cat",
            vivienda=vivienda)
        otros_cat = Categoria.objects.create(
            nombre="Otros",
            vivienda=vivienda)
        gasto_custom_cat = Gasto.objects.create(
            monto=1000,
            creado_por=test_user_1.get_vu(),
            categoria=categoria)
        self.assertEqual(
            Gasto.objects.filter(categoria=categoria).count(),
            1)
        self.assertEqual(
            Gasto.objects.filter(categoria=otros_cat).count(),
            0)

        response = self.client.post(
            "/vivienda/categorias/delete/",
            data={
                "categoria": categoria.id
            },
            follow=True)

        self.assertRedirects(response, self.url)
        self.assertTrue(Categoria.objects.filter(
            id=categoria.id).exists())
        self.assertTrue(Categoria.objects.filter(
            nombre=categoria.nombre,
            vivienda=vivienda).exists())
        self.assertEqual(
            Gasto.objects.filter(categoria=categoria).count(),
            1)
        self.assertEqual(
            Gasto.objects.filter(categoria=otros_cat).count(),
            0)


class ItemListTest(TestCase):

    url = "/vivienda/items/"

    def test_not_logged_user_cant_see_items(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        self.client.logout()
        response = self.client.get(
            self.url,
            follow=True)

        self.assertRedirects(
            response,
            "/accounts/login/?next=%s" % (self.url))

    def test_homeless_user_cant_see_items(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        test_user.get_vu().leave()
        response = self.client.get(
            self.url,
            follow=True)

        self.assertRedirects(
            response,
            "/error/")
        self.assertContains(
            response,
            "Para tener acceso a esta página debe pertenecer a una vivienda")

    def test_user_can_see_items_of_his_vivienda(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        vivienda = test_user.get_vivienda()
        custom_item = Item.objects.create(
            nombre="custom1",
            vivienda=vivienda)

        response = self.client.get(
            self.url,
            follow=True)

        for item in vivienda.get_items():
            self.assertContains(response, item.nombre)

    def test_user_cant_see_items_of_other_vivienda(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        vivienda = test_user.get_vivienda()
        other_vivienda = Vivienda.objects.exclude(id=vivienda.id).first()
        custom_item = Item.objects.create(
            nombre="custom1",
            vivienda=other_vivienda)

        response = self.client.get(
            self.url,
            follow=True)

        self.assertNotContains(response, custom_item.nombre)


class NewItemTest(TestCase):

    url = "/vivienda/items/new/"

    def test_not_logged_user_cant_create_item(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        self.client.logout()
        response = self.client.post(
            self.url,
            data={
                "nombre": "customizimo",
                "unidad_medida" : "kg"
            },
            follow=True)

        self.assertRedirects(
            response,
            "/accounts/login/?next=%s" % (self.url))

    def test_homeless_user_cant_create_item(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        test_user.get_vu().leave()
        response = self.client.post(
            self.url,
            data={
                "nombre": "customizimo",
                "unidad_medida" : "kg"
            },
            follow=True)

        self.assertRedirects(
            response,
            "/error/")
        self.assertContains(
            response,
            "Para tener acceso a esta página debe pertenecer a una vivienda")

    def test_user_can_create_custom_item(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        vivienda = test_user.get_vivienda()
        original_item_count = vivienda.get_items().count()
        self.assertFalse(Item.objects.filter(
            nombre="customizimo",
            vivienda=vivienda).exists())

        response = self.client.post(
            self.url,
            data={
                "nombre": "customizimo",
                "unidad_medida" : "kg"
            },
            follow=True)

        self.assertEqual(
            vivienda.get_items().count(),
            original_item_count + 1)
        self.assertRedirects(response, "/vivienda/items/")
        self.assertTrue(Item.objects.filter(
            nombre="customizimo",
            vivienda=vivienda).exists())
        self.assertEqual(
            Item.objects.filter(nombre="customizimo").count(),
            1)

    def test_user_cant_create_item_with_broken_POST(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        vivienda = test_user.get_vivienda()
        original_item_count = vivienda.get_items().count()
        self.assertFalse(Item.objects.filter(
            nombre="customizimo",
            vivienda=vivienda).exists())

        response = self.client.post(
            self.url,
            data={
                "weird_key": "SQLInj",
                "unidad_medida" : "kg"
            },
            follow=True)

        self.assertRedirects(response, "/vivienda/items/")
        self.assertContains(
            response,
            "Se produjo un error procesando los datos ingresados")
        self.assertFalse(Item.objects.filter(
            nombre="customizimo",
            vivienda=vivienda).exists())
        self.assertEqual(
            vivienda.get_items().count(),
            original_item_count)


class EditItemViewTest(TestCase):

    def test_not_logged_user_cant_edit_item(self):
        self.fail()

    def test_homeless_user_cant_edit_item(self):
        self.fail()

    def test_user_cant_edit_item_of_other_vivienda(self):
        self.fail()

    def test_user_can_edit_item_of_own_vivienda(self):
        self.fail()

    def test_user_cant_edit_item_with_broken_POST(self):
        self.fail()