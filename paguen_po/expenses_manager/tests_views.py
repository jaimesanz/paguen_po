# -*- coding: utf-8 -*-
from django.test import TestCase
from django.utils import timezone

from .models import ViviendaUsuario, Invitacion, Gasto, \
    ConfirmacionGasto, ListaCompras, \
    ItemLista
from budgets.models import Presupuesto
from groceries.models import Item, ListaCompras, ItemLista
from periods.models import YearMonth
from vacations.models import UserIsOut
from categories.models import Categoria
from households.models import Vivienda, ViviendaUsuario, Invitacion
from users.models import ProxyUser
from .test_utils import test_the_basics_not_logged_in, \
    execute_test_the_basics_logged_in, \
    execute_test_the_basics_not_logged_in_restricted, get_test_user_and_login, \
    get_test_user_with_vivienda_and_login, has_logged_navbar_with_viv, \
    has_logged_navbar_without_viv, get_vivienda_with_1_user, get_lone_user, \
    get_setup_viv_2_users_viv_1_user_cat_1_gastos_3, \
    execute_test_basics_logged_with_viv, has_not_logged_navbar, \
    get_setup_with_gastos_items_and_listas
from .views import home, about, error, nueva_vivienda, manage_users, \
    invites_list, gastos, presupuestos, graphs_presupuestos


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

        has_logged_navbar_with_viv(self, response, test_user)


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
        self.assertRedirects(response, "/")
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
        self.assertRedirects(response, "/")
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


class NewGastoViewTest(TestCase):

    def test_user_tries_to_create_new_gasto_w_incomplete_POST_request(self):
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

        self.assertRedirects(response, "/gastos/")
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

        not_today = timezone.now().date() - timezone.timedelta(weeks=20)

        response = self.client.post(
            "/nuevo_gasto/",
            data={
                "categoria": dummy_categoria.id,
                "monto": 232,
                "is_paid": "no",
                "fecha_pago": not_today
            },
            follow=True)

        self.assertRedirects(response, "/gastos/")
        pending_gastos = Gasto.objects.filter(
            creado_por__vivienda=test_user_1.get_vivienda(),
            estado__estado="pendiente")
        for gasto in pending_gastos:
            self.assertContains(response, gasto.monto)
            self.assertContains(
                response, "href=\"/detalle_gasto/%d/\"" % gasto.id)
        self.assertNotContains(response, gasto_3.monto)
        self.assertNotContains(
            response, "href=\"/detalle_gasto/%d/\"" % gasto_3.id)

    def test_user_can_create_paid_gasto(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)

        today = timezone.now().date()

        response = self.client.post(
            "/nuevo_gasto/",
            data={
                "categoria": dummy_categoria.id,
                "monto": 232,
                "is_paid": "yes",
                "fecha_pago": today
            },
            follow=True)

        self.assertRedirects(response, "/gastos/")
        paid_gastos = Gasto.objects.filter(
            creado_por__vivienda=test_user_1.get_vivienda(),
            estado__estado="pagado")
        self.assertEqual(
            paid_gastos.count(),
            0)
        pending_confirm_gastos = Gasto.objects.filter(
            creado_por__vivienda=test_user_1.get_vivienda(),
            estado__estado="pendiente_confirmacion")
        self.assertEqual(
            pending_confirm_gastos.count(),
            1)
        for gasto in pending_confirm_gastos:
            self.assertContains(response, gasto.monto)
            self.assertContains(
                response, "href=\"/detalle_gasto/%d/\"" % gasto.id)
        self.assertNotContains(response, gasto_3.monto)
        self.assertNotContains(
            response, "href=\"/detalle_gasto/%d/\"" % gasto_3.id)

    def test_user_can_create_paid_gasto_with_custom_old_fecha_pago(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)

        not_today = timezone.now().date() - timezone.timedelta(weeks=20)
        not_this_period, __ = YearMonth.objects.get_or_create(
            year=not_today.year,
            month=not_today.month)
        unique_categoria = Categoria.objects.create(
            nombre="oldies_cat",
            vivienda=test_user_1.get_vivienda())

        response = self.client.post(
            "/nuevo_gasto/",
            data={
                "categoria": unique_categoria.id,
                "monto": 232,
                "is_paid": "yes",
                "fecha_pago": not_today
            },
            follow=True)

        self.assertRedirects(response, "/gastos/")
        new_gasto = Gasto.objects.get(categoria=unique_categoria)
        self.assertEqual(new_gasto.fecha_pago, not_today)
        self.assertEqual(new_gasto.year_month, not_this_period)
        self.assertFalse(new_gasto.is_paid())
        self.assertTrue(new_gasto.is_pending_confirm())

    def test_user_CANT_create_paid_gasto_with_custom_future_fecha_pago(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)

        not_today = timezone.now().date() + timezone.timedelta(weeks=20)
        YearMonth.objects.get_or_create(
            year=not_today.year,
            month=not_today.month)
        unique_categoria = Categoria.objects.create(
            nombre="future_cat",
            vivienda=test_user_1.get_vivienda())

        response = self.client.post(
            "/nuevo_gasto/",
            data={
                "categoria": unique_categoria.id,
                "monto": 232,
                "is_paid": "yes",
                "fecha_pago": not_today
            },
            follow=True)

        self.assertRedirects(response, "/gastos/")
        self.assertFalse(Gasto.objects.filter(
            categoria=unique_categoria).exists())
        self.assertContains(
            response,
            "No puede crear un Gasto para una fecha futura.")


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
            response, "href=\"/detalle_gasto/%d/\"" % gasto_1.id)
        self.assertContains(response, gasto_2.monto)
        self.assertContains(
            response, "href=\"/detalle_gasto/%d/\"" % gasto_2.id)
        # check that logged user can't see the gasto from the other vivienda
        self.assertNotContains(response, gasto_3.monto)
        self.assertNotContains(
            response, "href=\"/detalle_gasto/%d/\"" % gasto_3.id)


class GastoViviendaPendingConfirmListViewTest(TestCase):

    url = "/gastos/"

    def test_user_can_see_pending_confirm_gastos_only_of_his_vivienda(self):
        (test_user_1,
         test_user_2,
         test_user_3,
         dummy_categoria,
         gasto_1,
         gasto_2,
         gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)

        test_user_1.get_vu().pay(gasto_1)
        test_user_2.get_vu().pay(gasto_2)
        test_user_3.get_vu().pay(gasto_3)

        response = self.client.get(
            self.url,
            follow=True
        )
        # check that logged user can see both gastos
        self.assertContains(response, dummy_categoria.nombre)
        self.assertContains(response, gasto_1.monto)
        self.assertContains(
            response, "href=\"/detalle_gasto/%d/\"" % gasto_1.id)
        self.assertContains(response, gasto_2.monto)
        self.assertContains(
            response, "href=\"/detalle_gasto/%d/\"" % gasto_2.id)
        # check that logged user can't see the gasto from the other vivienda
        self.assertNotContains(response, gasto_3.monto)
        self.assertNotContains(
            response, "href=\"/detalle_gasto/%d/\"" % gasto_3.id)


class GastoViviendaPaidListViewTest(TestCase):

    def test_basics_paid_gasto_list_url(self):
        execute_test_the_basics_not_logged_in_restricted(self, "/gastos/")

    def test_basics_paid_gasto_list_with_vivienda(self):
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
        gasto_1.confirm_pay(test_user_1.get_vu())
        gasto_2.confirm_pay(test_user_2.get_vu())
        gasto_3.confirm_pay(test_user_3.get_vu())

        response = self.client.get("/gastos/", follow=True)
        # check that logged user can see both gastos
        self.assertContains(response, dummy_categoria.nombre)
        self.assertContains(
            response, "href=\"/detalle_gasto/%d/\"" % gasto_1.id)
        self.assertContains(
            response, "href=\"/detalle_gasto/%d/\"" % gasto_2.id)
        # check that logged user can't see the gasto from the other vivienda
        self.assertNotContains(
            response, "href=\"/detalle_gasto/%d/\"" % gasto_3.id)


class GastoViviendaPendingConfirmViewTest(TestCase):

    def test_not_logged_user_cant_confirm_gasto(self):
        (test_user_1,
         test_user_2,
         test_user_3,
         dummy_categoria,
         gasto_1,
         gasto_2,
         gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)
        url = "/confirm/%d/" % (gasto_1.id)
        test_user_2.get_vu().pay(gasto_1)

        self.client.logout()

        response = self.client.post(
            url,
            data={
                "csrfmiddlewaretoken": "rubbish"
            },
            follow=True)
        self.assertRedirects(
            response,
            "/accounts/login/?next=/confirm/%d/" % (gasto_1.id))
        has_not_logged_navbar(self, response)

    def test_homeless_cant_confirm_gasto(self):
        (test_user_1,
         test_user_2,
         test_user_3,
         dummy_categoria,
         gasto_1,
         gasto_2,
         gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)
        url = "/confirm/%d/" % (gasto_1.id)
        test_user_2.get_vu().pay(gasto_1)

        test_user_1.leave()

        response = self.client.post(
            url,
            data={
                "csrfmiddlewaretoken": "rubbish"
            },
            follow=True)

        self.assertRedirects(
            response,
            "/error/")
        self.assertContains(
            response,
            "Para tener acceso a esta página debe pertenecer a una vivienda")

    def test_outsider_cant_confirm_gasto(self):
        (test_user_1,
         test_user_2,
         test_user_3,
         dummy_categoria,
         gasto_1,
         gasto_2,
         gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)

        # roommate for user3 (so that the Gasto doesn't immediately get a
        # confirmed paid state)
        test_user_4 = ProxyUser.objects.create(
            username="test_user_4", email="d@d.com")
        test_user_4_viv = ViviendaUsuario.objects.create(
            vivienda=test_user_3.get_vivienda(), user=test_user_4)

        test_user_3.get_vu().pay(gasto_3)  # is pending_confirm; user4 must
        # still confirm
        url = "/confirm/%d/" % (gasto_3.id)

        response = self.client.post(
            url,
            data={
                "csrfmiddlewaretoken": "rubbish"
            },
            follow=True)

        self.assertRedirects(
            response,
            "/error/")
        self.assertContains(
            response,
            "Usted no está autorizado para ver esta página")
        # assert the Gasto did not change
        self.assertFalse(Gasto.objects.get(id=gasto_3.id).is_paid())
        self.assertTrue(Gasto.objects.get(id=gasto_3.id).is_pending_confirm())
        self.assertFalse(Gasto.objects.get(id=gasto_3.id).is_pending())

    def test_user_can_see_confirm_button(self):
        (test_user_1,
         test_user_2,
         test_user_3,
         dummy_categoria,
         gasto_1,
         gasto_2,
         gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)

        url = "/confirm/%d/" % (gasto_1.id)
        test_user_2.get_vu().pay(gasto_1)

        response = self.client.get(
            url,
            follow=True)

        self.assertContains(response, "Confirmar")

    def test_user_cant_see_confirm_button_if_he_already_confirmed(self):
        (test_user_1,
         test_user_2,
         test_user_3,
         dummy_categoria,
         gasto_1,
         gasto_2,
         gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)

        url = "/confirm/%d/" % (gasto_1.id)
        test_user_1.get_vu().pay(gasto_1)

        response = self.client.get(
            url,
            follow=True)

        self.assertNotContains(response, "Confirmar")

    def test_user_can_confirm_gasto(self):
        (test_user_1,
         test_user_2,
         test_user_3,
         dummy_categoria,
         gasto_1,
         gasto_2,
         gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)

        # third roommate (so that the Gasto doesn't immediately get a
        # confirmed paid state when the logged user confirms)
        test_user_4 = ProxyUser.objects.create(
            username="test_user_4", email="d@d.com")
        test_user_4_viv = ViviendaUsuario.objects.create(
            vivienda=test_user_1.get_vivienda(), user=test_user_4)
        self.assertEqual(
            test_user_1.get_vivienda().get_active_users().count(),
            3
        )
        url = "/confirm/%d/" % (gasto_1.id)
        test_user_2.get_vu().pay(gasto_1)

        response = self.client.post(
            url,
            data={
                "csrfmiddlewaretoken": "rubbish"
            },
            follow=True)

        self.assertRedirects(response, "/detalle_gasto/%d/" % (gasto_1.id))
        self.assertContains(response, "Gasto confirmado.")
        # assert the Gasto DID change
        self.assertFalse(Gasto.objects.get(id=gasto_1.id).is_paid())
        self.assertTrue(Gasto.objects.get(id=gasto_1.id).is_pending_confirm())
        self.assertFalse(Gasto.objects.get(id=gasto_1.id).is_pending())
        self.assertTrue(
            ConfirmacionGasto.objects.get(
                vivienda_usuario=test_user_1.get_vu(),
                gasto=gasto_1
            ).confirmed
        )

        self.assertTrue(
            ConfirmacionGasto.objects.get(
                vivienda_usuario=test_user_2.get_vu(),
                gasto=gasto_1
            ).confirmed
        )

        self.assertFalse(
            ConfirmacionGasto.objects.get(
                vivienda_usuario=test_user_4.get_vu(),
                gasto=gasto_1
            ).confirmed
        )

    def test_user_can_confirm_gasto_and_it_changes_to_paid(self):
        (test_user_1,
         test_user_2,
         test_user_3,
         dummy_categoria,
         gasto_1,
         gasto_2,
         gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)

        url = "/confirm/%d/" % (gasto_1.id)
        test_user_2.get_vu().pay(gasto_1)

        response = self.client.post(
            url,
            data={
                "csrfmiddlewaretoken": "rubbish"
            },
            follow=True)

        self.assertRedirects(response, "/detalle_gasto/%d/" % (gasto_1.id))
        self.assertNotContains(response, "Gasto confirmado.")
        self.assertContains(response, "El gasto fue confirmado por todos los "
                                      "usuarios pertinentes.")

        # assert the Gasto DID change
        self.assertTrue(Gasto.objects.get(id=gasto_1.id).is_paid())
        self.assertFalse(Gasto.objects.get(id=gasto_1.id).is_pending_confirm())
        self.assertFalse(Gasto.objects.get(id=gasto_1.id).is_pending())
        self.assertTrue(
            ConfirmacionGasto.objects.get(
                vivienda_usuario=test_user_1.get_vu(),
                gasto=gasto_1
            ).confirmed
        )

        self.assertTrue(
            ConfirmacionGasto.objects.get(
                vivienda_usuario=test_user_2.get_vu(),
                gasto=gasto_1
            ).confirmed
        )

    def test_user_cant_confirm_more_than_once(self):
        (test_user_1,
         test_user_2,
         test_user_3,
         dummy_categoria,
         gasto_1,
         gasto_2,
         gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)

        # third roommate (so that the Gasto doesn't immediately get a
        # confirmed paid state when the logged user confirms)
        test_user_4 = ProxyUser.objects.create(
            username="test_user_4", email="d@d.com")
        test_user_4_viv = ViviendaUsuario.objects.create(
            vivienda=test_user_1.get_vivienda(), user=test_user_4)
        self.assertEqual(
            test_user_1.get_vivienda().get_active_users().count(),
            3
        )
        url = "/confirm/%d/" % (gasto_1.id)
        test_user_2.get_vu().pay(gasto_1)
        test_user_1.get_vu().confirm(gasto_1)

        response = self.client.post(
            url,
            data={
                "csrfmiddlewaretoken": "rubbish"
            },
            follow=True)

        self.assertRedirects(response, "/detalle_gasto/%d/" % (gasto_1.id))
        self.assertContains(response, "Usted ya confirmó este Gasto")

        # assert the Gasto did NOT change
        self.assertFalse(Gasto.objects.get(id=gasto_1.id).is_paid())
        self.assertTrue(Gasto.objects.get(id=gasto_1.id).is_pending_confirm())
        self.assertFalse(Gasto.objects.get(id=gasto_1.id).is_pending())
        self.assertTrue(
            ConfirmacionGasto.objects.get(
                vivienda_usuario=test_user_1.get_vu(),
                gasto=gasto_1
            ).confirmed
        )

        self.assertTrue(
            ConfirmacionGasto.objects.get(
                vivienda_usuario=test_user_2.get_vu(),
                gasto=gasto_1
            ).confirmed
        )

        self.assertFalse(
            ConfirmacionGasto.objects.get(
                vivienda_usuario=test_user_4.get_vu(),
                gasto=gasto_1
            ).confirmed
        )


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
            response, "href=\"/detalle_gasto/%d\"/" % gasto_3.id)

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
            response, "href=\"/detalle_gasto/%d\"/" % gasto_3.id)

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
            0)
        self.assertEqual(
            Gasto.objects.filter(
                creado_por__vivienda=test_user_1.get_vivienda(),
                estado__estado="pendiente_confirmacion")
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
        gasto_1.confirm_pay(test_user_1.get_vu())
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
            0)
        self.assertEqual(
            Gasto.objects.filter(
                creado_por__vivienda=test_user_1.get_vivienda(),
                estado__estado="pendiente_confirmacion")
            .count(),
            1)
        self.assertNotContains(response, "<a href=\"/detalle_lista/")
        self.assertNotContains(response, "<td><b>Lista compras:</b></td>")

    def test_user_cant_pay_a_pending_confirm_gasto(self):
        (test_user_1,
         test_user_2,
         test_user_3,
         dummy_categoria,
         gasto_1,
         gasto_2,
         gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)
        test_user_1.get_vu().pay(gasto_1)

        # user attempts to pay it again, but it no longer has a "pending" state
        response = self.client.post(
            "/detalle_gasto/%d/" % (gasto_1.id),
            data={"submit": "submit"},
            follow=True)
        self.assertRedirects(response, "/error/")
        self.assertContains(response, "El gasto ya se encuentra pagado.")
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
            0)

        self.assertEqual(
            Gasto.objects.filter(
                creado_por__vivienda=test_user_1.get_vivienda(),
                estado__estado="pendiente_confirmacion")
            .count(),
            1)

    def test_roommate_cannot_pay_paid_gasto(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)
        gasto_2.confirm_pay(test_user_2.get_vu())
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


class GastoEditViewTest(TestCase):

    def setup(self):
        """
        Creates a database with the necessary objects to execute most tests
        for this TestCase.
        :return: Dict
        """
        (test_user_1,
         test_user_2,
         test_user_3,
         dummy_categoria,
         gasto_1,
         gasto_2,
         gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)

        db = dict()
        db["test_user_1"] = test_user_1
        db["test_user_2"] = test_user_2
        db["test_user_3"] = test_user_3
        db["dummy_categoria"] = dummy_categoria
        db["gasto_1"] = gasto_1
        db["gasto_2"] = gasto_2
        db["gasto_3"] = gasto_3

        for i in range(1, 4):
            gasto = db["gasto_" + str(i)]
            db["original_date_" + str(i)] = gasto.fecha_pago
            db["original_monto_" + str(i)] = gasto.monto
            db["original_year_month_" + str(i)] = gasto.year_month
            db["url_gasto_" + str(i)] = "/edit_gasto/%d/" % (gasto.id)

        db["not_today"] = timezone.now().date() - timezone.timedelta(weeks=20)

        return db

    def assert_gasto_did_not_change(self, db, gasto_index):
        """
        Asserts that the Gasto given by the given index has not changed.
        :param db: Dict
        :param gasto_index: Integer
        """
        gasto = db["gasto_" + str(gasto_index)]
        self.assertEqual(
            Gasto.objects.get(id=gasto.id).fecha_pago,
            db["original_date_" + str(gasto_index)]
        )
        self.assertEqual(
            Gasto.objects.get(id=gasto.id).monto,
            db["original_monto_" + str(gasto_index)]
        )
        self.assertEqual(
            Gasto.objects.get(id=gasto.id).year_month,
            db["original_year_month_" + str(gasto_index)]
        )

    def test_not_logged_user_cant_edit(self):
        db = self.setup()
        gasto_1 = db["gasto_1"]

        self.client.logout()

        response = self.client.post(
            db["url_gasto_1"],
            data={
                "csrfmiddlewaretoken": "rubbish",
                "monto": 1000,
                "fecha_pago": db["not_today"]
            },
            follow=True)

        self.assertRedirects(
            response,
            "/accounts/login/?next=/edit_gasto/%d/" % (gasto_1.id))
        has_not_logged_navbar(self, response)

        self.assert_gasto_did_not_change(db, 1)

    def test_homeless_user_cant_edit(self):
        db = self.setup()
        gasto_1 = db["gasto_1"]
        test_user_1 = db["test_user_1"]

        test_user_1.leave()

        response = self.client.post(
            db["url_gasto_1"],
            data={
                "csrfmiddlewaretoken": "rubbish",
                "monto": 1000,
                "fecha_pago": db["not_today"]
            },
            follow=True)

        self.assertRedirects(
            response,
            "/error/")
        self.assertContains(
            response,
            "Para tener acceso a esta página debe pertenecer a una vivienda")

        self.assert_gasto_did_not_change(db, 1)

    def test_outsider_user_cant_edit(self):
        db = self.setup()

        response = self.client.post(
            db["url_gasto_3"],
            data={
                "csrfmiddlewaretoken": "rubbish",
                "monto": 1000,
                "fecha_pago": db["not_today"]
            },
            follow=True)

        self.assertRedirects(
            response,
            "/error/")
        self.assertContains(
            response,
            "Usted no está autorizado para ver esta página.")

        self.assert_gasto_did_not_change(db, 3)

    def test_user_can_edit_own_pending_gasto(self):
        db = self.setup()
        gasto_1 = db["gasto_1"]

        response = self.client.post(
            db["url_gasto_1"],
            data={
                "csrfmiddlewaretoken": "rubbish",
                "monto": 1000,
                "fecha_pago": db["not_today"]
            },
            follow=True)

        self.assertRedirects(
            response,
            "/detalle_gasto/%d/" % gasto_1.id)
        self.assertContains(
            response,
            "Gasto editado.")

        self.assertNotEqual(
            Gasto.objects.get(id=gasto_1.id).monto,
            db["original_monto_1"]
        )
        self.assertEqual(
            Gasto.objects.get(id=gasto_1.id).fecha_pago,
            db["original_date_1"]
        )
        self.assertEqual(
            Gasto.objects.get(id=gasto_1.id).year_month,
            db["original_year_month_1"]
        )

        self.assertNotEqual(
            Gasto.objects.get(id=gasto_1.id).fecha_pago,
            db["not_today"]
        )
        self.assertEqual(
            Gasto.objects.get(id=gasto_1.id).monto,
            1000
        )

        self.assertFalse(
            Gasto.objects.get(id=gasto_1.id).is_pending_confirm()
        )
        self.assertFalse(
            Gasto.objects.get(id=gasto_1.id).is_paid()
        )
        self.assertTrue(
            Gasto.objects.get(id=gasto_1.id).is_pending()
        )

    def test_user_can_edit_other_user_pending_gasto(self):
        db = self.setup()
        gasto = db["gasto_2"]

        response = self.client.post(
            db["url_gasto_2"],
            data={
                "csrfmiddlewaretoken": "rubbish",
                "monto": 1000,
                "fecha_pago": db["not_today"]
            },
            follow=True)

        self.assertRedirects(
            response,
            "/detalle_gasto/%d/" % gasto.id)
        self.assertContains(
            response,
            "Gasto editado.")

        self.assertNotEqual(
            Gasto.objects.get(id=gasto.id).monto,
            db["original_monto_2"]
        )
        self.assertEqual(
            Gasto.objects.get(id=gasto.id).fecha_pago,
            db["original_date_2"]
        )
        self.assertEqual(
            Gasto.objects.get(id=gasto.id).year_month,
            db["original_year_month_2"]
        )

        self.assertNotEqual(
            Gasto.objects.get(id=gasto.id).fecha_pago,
            db["not_today"]
        )
        self.assertEqual(
            Gasto.objects.get(id=gasto.id).monto,
            1000
        )

        self.assertFalse(
            Gasto.objects.get(id=gasto.id).is_pending_confirm()
        )
        self.assertFalse(
            Gasto.objects.get(id=gasto.id).is_paid()
        )
        self.assertTrue(
            Gasto.objects.get(id=gasto.id).is_pending()
        )

    def test_user_can_edit_own_pending_confirm_gasto(self):
        db = self.setup()

        gasto_1 = db["gasto_1"]
        db["test_user_1"].get_vu().pay(gasto_1)
        self.assertTrue(
            Gasto.objects.get(id=gasto_1.id).is_pending_confirm()
        )

        response = self.client.post(
            db["url_gasto_1"],
            data={
                "csrfmiddlewaretoken": "rubbish",
                "monto": 1000,
                "fecha_pago": db["not_today"]
            },
            follow=True)

        self.assertRedirects(
            response,
            "/detalle_gasto/%d/" % db["gasto_1"].id)
        self.assertContains(
            response,
            "Gasto editado. Se cambió el estado a pendiente.")

        self.assertNotEqual(
            Gasto.objects.get(id=gasto_1.id).fecha_pago,
            db["original_date_1"]
        )
        self.assertNotEqual(
            Gasto.objects.get(id=gasto_1.id).monto,
            db["original_monto_1"]
        )
        self.assertNotEqual(
            Gasto.objects.get(id=gasto_1.id).year_month,
            db["original_year_month_1"]
        )

        self.assertEqual(
            Gasto.objects.get(id=gasto_1.id).fecha_pago,
            db["not_today"]
        )
        self.assertEqual(
            Gasto.objects.get(id=gasto_1.id).monto,
            1000
        )

        self.assertTrue(
            Gasto.objects.get(id=gasto_1.id).is_pending_confirm()
        )
        self.assertFalse(
            Gasto.objects.get(id=gasto_1.id).is_paid()
        )
        self.assertFalse(
            Gasto.objects.get(id=gasto_1.id).is_pending()
        )

        self.assertTrue(
            ConfirmacionGasto.objects.get(
                gasto=gasto_1,
                vivienda_usuario=db["test_user_1"].get_vu()).confirmed
        )

    def test_user_cant_edit_other_user_pending_confirm_gasto(self):
        db = self.setup()

        gasto = db["gasto_2"]
        db["test_user_2"].get_vu().pay(gasto)
        db["original_date_2"] = Gasto.objects.get(id=gasto.id).fecha_pago
        db["original_year_month_2"] = Gasto.objects.get(id=gasto.id).year_month
        self.assertTrue(
            Gasto.objects.get(id=gasto.id).is_pending_confirm()
        )

        response = self.client.post(
            db["url_gasto_2"],
            data={
                "csrfmiddlewaretoken": "rubbish",
                "monto": 1000,
                "fecha_pago": db["not_today"]
            },
            follow=True)

        self.assertRedirects(
            response,
            "/detalle_gasto/%d/" % gasto.id)
        self.assertContains(
            response,
            "No tiene permiso para editar este Gasto")

        self.assert_gasto_did_not_change(db, 2)

        self.assertTrue(
            Gasto.objects.get(id=gasto.id).is_pending_confirm()
        )
        self.assertFalse(
            Gasto.objects.get(id=gasto.id).is_paid()
        )
        self.assertFalse(
            Gasto.objects.get(id=gasto.id).is_pending()
        )

    def test_user_can_edit_own_paid_gasto(self):
        db = self.setup()

        gasto_1 = db["gasto_1"]
        db["test_user_1"].get_vu().pay(gasto_1)
        db["test_user_2"].get_vu().confirm(gasto_1)
        self.assertTrue(
            Gasto.objects.get(id=gasto_1.id).is_paid()
        )

        response = self.client.post(
            db["url_gasto_1"],
            data={
                "csrfmiddlewaretoken": "rubbish",
                "monto": 1000,
                "fecha_pago": db["not_today"]
            },
            follow=True)

        self.assertRedirects(
            response,
            "/detalle_gasto/%d/" % db["gasto_1"].id)
        self.assertContains(
            response,
            "Gasto editado. Se cambió el estado a pendiente.")

        self.assertNotEqual(
            Gasto.objects.get(id=gasto_1.id).fecha_pago,
            db["original_date_1"]
        )
        self.assertNotEqual(
            Gasto.objects.get(id=gasto_1.id).monto,
            db["original_monto_1"]
        )
        self.assertNotEqual(
            Gasto.objects.get(id=gasto_1.id).year_month,
            db["original_year_month_1"]
        )

        self.assertEqual(
            Gasto.objects.get(id=gasto_1.id).fecha_pago,
            db["not_today"]
        )
        self.assertEqual(
            Gasto.objects.get(id=gasto_1.id).monto,
            1000
        )

        self.assertTrue(
            Gasto.objects.get(id=gasto_1.id).is_pending_confirm()
        )
        self.assertFalse(
            Gasto.objects.get(id=gasto_1.id).is_paid()
        )
        self.assertFalse(
            Gasto.objects.get(id=gasto_1.id).is_pending()
        )

    def test_user_cant_edit_other_user_paid_gasto(self):
        db = self.setup()

        gasto = db["gasto_2"]
        db["test_user_2"].get_vu().pay(gasto)
        db["test_user_1"].get_vu().confirm(gasto)
        db["original_date_2"] = Gasto.objects.get(id=gasto.id).fecha_pago
        db["original_year_month_2"] = Gasto.objects.get(id=gasto.id).year_month
        self.assertTrue(
            Gasto.objects.get(id=gasto.id).is_paid()
        )

        response = self.client.post(
            db["url_gasto_2"],
            data={
                "csrfmiddlewaretoken": "rubbish",
                "monto": 1000,
                "fecha_pago": db["not_today"]
            },
            follow=True)

        self.assertRedirects(
            response,
            "/detalle_gasto/%d/" % gasto.id)
        self.assertContains(
            response,
            "No tiene permiso para editar este Gasto")

        self.assert_gasto_did_not_change(db, 2)

        self.assertFalse(
            Gasto.objects.get(id=gasto.id).is_pending_confirm()
        )
        self.assertTrue(
            Gasto.objects.get(id=gasto.id).is_paid()
        )
        self.assertFalse(
            Gasto.objects.get(id=gasto.id).is_pending()
        )

    def test_user_cant_edit_paid_gasto_with_broken_date(self):
        db = self.setup()

        gasto = db["gasto_1"]
        db["test_user_1"].get_vu().pay(gasto)
        db["test_user_2"].get_vu().confirm(gasto)
        db["original_date_1"] = Gasto.objects.get(id=gasto.id).fecha_pago
        db["original_year_month_1"] = Gasto.objects.get(id=gasto.id).year_month
        self.assertTrue(
            Gasto.objects.get(id=gasto.id).is_paid()
        )

        response = self.client.post(
            db["url_gasto_1"],
            data={
                "csrfmiddlewaretoken": "rubbish",
                "monto": 1000,
                "fecha_pago": "some_random_string"
            },
            follow=True)

        self.assertRedirects(
            response,
            "/edit_gasto/%d/" % gasto.id)
        self.assertContains(
            response,
            "La fecha ingresada no es válida")

        self.assert_gasto_did_not_change(db, 1)

        self.assertFalse(
            Gasto.objects.get(id=gasto.id).is_pending_confirm()
        )
        self.assertTrue(
            Gasto.objects.get(id=gasto.id).is_paid()
        )
        self.assertFalse(
            Gasto.objects.get(id=gasto.id).is_pending()
        )

    def test_user_cant_post_negative_monto(self):
        db = self.setup()

        gasto = db["gasto_1"]
        self.assertTrue(
            Gasto.objects.get(id=gasto.id).is_pending()
        )

        response = self.client.post(
            db["url_gasto_1"],
            data={
                "csrfmiddlewaretoken": "rubbish",
                "monto": -1000,
                "fecha_pago": db["not_today"]
            },
            follow=True)

        self.assertRedirects(
            response,
            "/edit_gasto/%d/" % gasto.id)
        self.assertContains(
            response,
            "El monto ingresado debe ser un número mayor que 0.")

        self.assert_gasto_did_not_change(db, 1)

        self.assertFalse(
            Gasto.objects.get(id=gasto.id).is_pending_confirm()
        )
        self.assertFalse(
            Gasto.objects.get(id=gasto.id).is_paid()
        )
        self.assertTrue(
            Gasto.objects.get(id=gasto.id).is_pending()
        )

    def test_user_cant_post_random_string_as_monto(self):
        db = self.setup()

        gasto = db["gasto_1"]
        self.assertTrue(
            Gasto.objects.get(id=gasto.id).is_pending()
        )

        response = self.client.post(
            db["url_gasto_1"],
            data={
                "csrfmiddlewaretoken": "rubbish",
                "monto": "some_weird_string",
                "fecha_pago": db["not_today"]
            },
            follow=True)

        self.assertRedirects(
            response,
            "/edit_gasto/%d/" % gasto.id)
        self.assertContains(
            response,
            "El monto ingresado debe ser un número mayor que 0.")

        self.assert_gasto_did_not_change(db, 1)

        self.assertFalse(
            Gasto.objects.get(id=gasto.id).is_pending_confirm()
        )
        self.assertFalse(
            Gasto.objects.get(id=gasto.id).is_paid()
        )
        self.assertTrue(
            Gasto.objects.get(id=gasto.id).is_pending()
        )

    def test_user_can_see_edit_button_on_own_pending(self):
        db = self.setup()
        gasto = db["gasto_1"]
        url = "/detalle_gasto/%d/" % gasto.id
        response = self.client.get(
            url,
            follow=True)

        self.assertContains(
            response,
            "Editar")

    def test_user_can_see_edit_button_on_own_pending_confirm(self):
        db = self.setup()
        gasto = db["gasto_1"]
        db["test_user_1"].get_vu().pay(gasto)
        url = "/detalle_gasto/%d/" % gasto.id
        response = self.client.get(
            url,
            follow=True)

        self.assertContains(
            response,
            "Editar")

    def test_user_can_see_edit_button_on_own_paid(self):
        db = self.setup()
        gasto = db["gasto_1"]
        db["test_user_1"].get_vu().pay(gasto)
        db["test_user_2"].get_vu().confirm(gasto)
        url = "/detalle_gasto/%d/" % gasto.id

        response = self.client.get(
            url,
            follow=True)

        self.assertContains(
            response,
            "Editar")

    def test_user_can_see_edit_button_on_other_user_pending(self):
        db = self.setup()
        gasto = db["gasto_2"]
        url = "/detalle_gasto/%d/" % gasto.id

        response = self.client.get(
            url,
            follow=True)

        self.assertContains(
            response,
            "Editar")

    def test_user_cant_see_edit_button_on_other_user_pending_confirm(self):
        db = self.setup()
        gasto = db["gasto_2"]
        db["test_user_2"].get_vu().pay(gasto)
        url = "/detalle_gasto/%d/" % gasto.id

        response = self.client.get(
            url,
            follow=True)

        self.assertNotContains(
            response,
            "Editar")

    def test_user_cant_see_edit_button_on_other_user_paid(self):
        db = self.setup()
        gasto = db["gasto_2"]
        db["test_user_2"].get_vu().pay(gasto)
        db["test_user_1"].get_vu().confirm(gasto)
        url = "/detalle_gasto/%d/" % gasto.id

        response = self.client.get(
            url,
            follow=True)

        self.assertNotContains(
            response,
            "Editar")

    def test_user_cant_see_edit_transfer_form(self):
        db = self.setup()
        test_user_1 = db["test_user_1"]
        test_user_2 = db["test_user_2"]

        transfer_pos, transfer_neg = test_user_1.transfer(test_user_2, 1000)

        for transfer_id in [transfer_pos.id, transfer_neg.id]:
            url = "/edit_gasto/%d/" % transfer_id
            response = self.client.get(
                url,
                follow=True)
            self.assertRedirects(
                response,
                "/detalle_gasto/%d/" % transfer_id)

    def test_user_cant_see_edit_button_on_transfer(self):
        db = self.setup()
        test_user_1 = db["test_user_1"]
        test_user_2 = db["test_user_2"]

        transfer_pos, transfer_neg = test_user_1.transfer(test_user_2, 1000)

        url = "/detalle_gasto/%d/" % transfer_pos.id

        response = self.client.get(
            url,
            follow=True)

        self.assertNotContains(
            response,
            "Editar")

        url = "/detalle_gasto/%d/" % transfer_neg.id

        response = self.client.get(
            url,
            follow=True)

        self.assertNotContains(
            response,
            "Editar")

    def test_user_cant_change_fecha_pago_to_future_date(self):
        db = self.setup()

        gasto_1 = db["gasto_1"]
        db["test_user_1"].get_vu().pay(gasto_1)
        db["test_user_2"].get_vu().confirm(gasto_1)
        db["original_date_1"] = Gasto.objects.get(id=gasto_1.id).fecha_pago
        db["original_year_month_1"] = Gasto.objects.get(
            id=gasto_1.id).year_month
        self.assertTrue(
            Gasto.objects.get(id=gasto_1.id).is_paid()
        )

        future_date = timezone.now().date() + timezone.timedelta(weeks=20)

        response = self.client.post(
            db["url_gasto_1"],
            data={
                "csrfmiddlewaretoken": "rubbish",
                "monto": 1000,
                "fecha_pago": future_date
            },
            follow=True)

        self.assertRedirects(
            response,
            "/edit_gasto/%d/" % gasto_1.id)
        self.assertContains(
            response,
            "No puede crear un Gasto para una fecha futura.")

        self.assert_gasto_did_not_change(db, 1)

        self.assertFalse(
            Gasto.objects.get(id=gasto_1.id).is_pending_confirm()
        )
        self.assertTrue(
            Gasto.objects.get(id=gasto_1.id).is_paid()
        )
        self.assertFalse(
            Gasto.objects.get(id=gasto_1.id).is_pending()
        )


class GastoDeleteViewTest(TestCase):

    url = "/gastos/delete/"

    def setup(self):
        """
        Creates a database with the necessary objects to execute most tests
        for this TestCase.
        :return: Dict
        """
        (test_user_1,
         test_user_2,
         test_user_3,
         dummy_categoria,
         gasto_1,
         gasto_2,
         gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(
            self)

        db = dict()
        db["test_user_1"] = test_user_1
        db["test_user_2"] = test_user_2
        db["test_user_3"] = test_user_3
        db["dummy_categoria"] = dummy_categoria
        db["gasto_1"] = gasto_1
        db["gasto_2"] = gasto_2
        db["gasto_3"] = gasto_3

        for i in range(1, 4):
            gasto = db["gasto_" + str(i)]
            db["original_date_" + str(i)] = gasto.fecha_pago
            db["original_monto_" + str(i)] = gasto.monto
            db["original_year_month_" + str(i)] = gasto.year_month
            db["url_gasto_" + str(i)] = "/edit_gasto/%d/" % (gasto.id)

        db["not_today"] = timezone.now().date() - timezone.timedelta(weeks=20)

        return db

    def test_not_logged_cant_delete(self):
        db = self.setup()
        gasto = db["gasto_1"]

        self.client.logout()

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "gasto": gasto.id
            },
            follow=True)

        self.assertRedirects(
            response,
            "/accounts/login/?next=/gastos/delete/")
        has_not_logged_navbar(self, response)

    def test_homeless_cant_delete(self):
        db = self.setup()
        gasto = db["gasto_1"]
        test_user_1 = db["test_user_1"]

        test_user_1.leave()

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "gasto": gasto.id
            },
            follow=True)

        self.assertRedirects(
            response,
            "/error/")
        self.assertContains(
            response,
            "Para tener acceso a esta página debe pertenecer a una vivienda")

    def test_user_can_delete_own_pending_gasto(self):
        db = self.setup()
        gasto = db["gasto_1"]

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "gasto": gasto.id
            },
            follow=True)

        self.assertRedirects(
            response,
            "/gastos/")
        self.assertContains(
            response,
            "Gasto eliminado.")
        self.assertFalse(
            Gasto.objects.filter(id=gasto.id).exists()
        )

    def test_user_can_delete_own_pending_confirmation_gasto(self):
        db = self.setup()
        gasto = db["gasto_1"]
        db["test_user_1"].get_vu().pay(gasto)
        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "gasto": gasto.id
            },
            follow=True)

        self.assertRedirects(
            response,
            "/gastos/")
        self.assertContains(
            response,
            "Gasto eliminado.")
        self.assertFalse(
            Gasto.objects.filter(id=gasto.id).exists()
        )

    def test_user_can_delete_own_paid_gasto(self):
        db = self.setup()
        gasto = db["gasto_1"]
        db["test_user_1"].get_vu().pay(gasto)
        db["test_user_2"].get_vu().confirm(gasto)
        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "gasto": gasto.id
            },
            follow=True)

        self.assertRedirects(
            response,
            "/gastos/")
        self.assertContains(
            response,
            "Gasto eliminado.")
        self.assertFalse(
            Gasto.objects.filter(id=gasto.id).exists()
        )

    def test_user_can_delete_other_user_pending_gasto(self):
        db = self.setup()
        gasto = db["gasto_2"]

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "gasto": gasto.id
            },
            follow=True)

        self.assertRedirects(
            response,
            "/gastos/")
        self.assertContains(
            response,
            "Gasto eliminado.")
        self.assertFalse(
            Gasto.objects.filter(id=gasto.id).exists()
        )

    def test_user_cant_delete_other_user_pending_confirmation_gasto(self):
        db = self.setup()
        gasto = db["gasto_2"]
        db["test_user_2"].get_vu().pay(gasto)
        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "gasto": gasto.id
            },
            follow=True)

        self.assertRedirects(
            response,
            "/detalle_gasto/%d/" % gasto.id)
        self.assertContains(
            response,
            "No tiene permiso para eliminar este Gasto")
        self.assertTrue(
            Gasto.objects.filter(id=gasto.id).exists()
        )

    def test_user_cant_delete_other_user_paid_gasto(self):
        db = self.setup()
        gasto = db["gasto_2"]
        db["test_user_2"].get_vu().pay(gasto)
        db["test_user_1"].get_vu().confirm(gasto)
        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "gasto": gasto.id
            },
            follow=True)

        self.assertRedirects(
            response,
            "/detalle_gasto/%d/" % gasto.id)
        self.assertContains(
            response,
            "No tiene permiso para eliminar este Gasto")
        self.assertTrue(
            Gasto.objects.filter(id=gasto.id).exists()
        )

    def test_user_can_see_delete_btn_own_pending_gasto(self):
        db = self.setup()
        gasto = db["gasto_1"]
        url = "/edit_gasto/%d/" % gasto.id

        response = self.client.get(
            url,
            follow=True
        )

        self.assertContains(
            response,
            "Eliminar")

    def test_user_can_see_delete_btn_own_pending_confirmation_gasto(self):
        db = self.setup()
        gasto = db["gasto_1"]
        db["test_user_1"].get_vu().pay(gasto)
        url = "/edit_gasto/%d/" % gasto.id

        response = self.client.get(
            url,
            follow=True
        )

        self.assertContains(
            response,
            "Eliminar")

    def test_user_can_see_delete_btn_own_paid_gasto(self):
        db = self.setup()
        gasto = db["gasto_1"]
        db["test_user_1"].get_vu().pay(gasto)
        db["test_user_2"].get_vu().confirm(gasto)
        url = "/edit_gasto/%d/" % gasto.id

        response = self.client.get(
            url,
            follow=True
        )

        self.assertContains(
            response,
            "Eliminar")

    def test_user_can_see_delete_btn_other_user_pending_gasto(self):
        db = self.setup()
        gasto = db["gasto_2"]
        url = "/edit_gasto/%d/" % gasto.id

        response = self.client.get(
            url,
            follow=True
        )

        self.assertContains(
            response,
            "Eliminar")

    def test_user_cant_see_delete_btn_other_user_pending_confirmation_gasto(
            self):
        db = self.setup()
        gasto = db["gasto_2"]
        db["test_user_2"].get_vu().pay(gasto)
        url = "/edit_gasto/%d/" % gasto.id

        response = self.client.get(
            url,
            follow=True
        )

        self.assertNotContains(
            response,
            "Eliminar")

    def test_user_cant_see_delete_btn_other_user_paid_gasto(self):
        db = self.setup()
        gasto = db["gasto_2"]
        db["test_user_2"].get_vu().pay(gasto)
        db["test_user_1"].get_vu().confirm(gasto)
        url = "/edit_gasto/%d/" % gasto.id

        response = self.client.get(
            url,
            follow=True
        )

        self.assertNotContains(
            response,
            "Eliminar")


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

    # TODO adapt this test to only having 1 list per vivienda
    # def test_user_can_create_lista_simple(self):
    #     test_user = get_setup_with_gastos_items_and_listas(self)
    #     response = self.client.post(
    #         "/nueva_lista/",
    #         data={
    #             "csrfmiddlewaretoken": "rubbish",
    #             "max_item_index": 3,
    #             "item_1": "d1",
    #             "quantity_1": 10,
    #             "item_2": "d2",
    #             "quantity_2": 20,
    #             "item_3": "d3",
    #             "quantity_3": 30
    #         },
    #         follow=True)
    #
    #     self.assertEqual(
    #         ListaCompras.objects.filter(
    #             usuario_creacion__vivienda=test_user.get_vivienda()).count(),
    #         2)
    #     self.assertEqual(
    #         ListaCompras.objects.count(),
    #         3)
    #     lista = ListaCompras.objects.latest("fecha")
    #     self.assertRedirects(response, "/detalle_lista/%d/" % (lista.id))
    #     for item_lista in ItemLista.objects.filter(lista=lista):
    #         self.assertContains(
    #             response,
    #             "<td class=\"cantidad_solicitada\">%d (%s)</td>" % (
    #                 item_lista.cantidad_solicitada,
    #                 item_lista.item.unidad_medida))

    # TODO adapt this test to only having 1 list per vivienda
    # def test_user_can_create_lista_w_items_that_skip_index_numbers(self):
    #     test_user = get_setup_with_gastos_items_and_listas(self)
    #     response = self.client.post(
    #         "/nueva_lista/",
    #         data={
    #             "csrfmiddlewaretoken": "rubbish",
    #             "max_item_index": 3,
    #             "item_1": "d1",
    #             "quantity_1": 10,
    #             "item_3": "d3",
    #             "quantity_3": 30
    #         },
    #         follow=True)
    #
    #     lista = ListaCompras.objects.latest("fecha")
    #     self.assertEqual(
    #         lista.count_items(),
    #         2)
    #     self.assertRedirects(response, "/detalle_lista/%d/" % (lista.id))
    #     for item_lista in ItemLista.objects.filter(lista=lista):
    #         self.assertContains(
    #             response,
    #             "<td class=\"cantidad_solicitada\">%d (%s)</td>" % (
    #                 item_lista.cantidad_solicitada,
    #                 item_lista.item.unidad_medida))

    # TODO adapt this test to only having 1 list per vivienda
    # def test_user_can_create_lista_w_skip_item_and_empty_fields(self):
    #     test_user = get_setup_with_gastos_items_and_listas(self)
    #     response = self.client.post(
    #         "/nueva_lista/",
    #         data={
    #             "csrfmiddlewaretoken": "rubbish",
    #             "max_item_index": 3,
    #             "item_1": "d1",
    #             "quantity_1": 10,
    #             "item_2": "",
    #             "quantity_2": 2,
    #             "item_3": "d3",
    #             "quantity_3": 30
    #         },
    #         follow=True)
    #
    #     lista = ListaCompras.objects.latest("fecha")
    #     self.assertEqual(
    #         lista.count_items(),
    #         2)
    #     self.assertRedirects(response, "/detalle_lista/%d/" % (lista.id))
    #     for item_lista in ItemLista.objects.filter(lista=lista):
    #         self.assertContains(
    #             response,
    #             "<td class=\"cantidad_solicitada\">%d (%s)</td>" % (
    #                 item_lista.cantidad_solicitada,
    #                 item_lista.item.unidad_medida))


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
                "options": "descartar_items",
                "monto_total": 1000,
                str(item_lista_1.id): 1,
                str(item_lista_2.id): 2
            },
            follow=True)
        gasto = Gasto.objects.get(lista_compras=lista)
        self.assertFalse(gasto.is_paid())
        self.assertTrue(ListaCompras.objects.get(id=lista.id).is_done())
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
                "options": "descartar_items",
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
                "options": "descartar_items",
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
                "options": "rescatar_items",
                "monto_total": 1000,
                str(item_lista_2.id): 2
            },
            follow=True)
        gasto = Gasto.objects.get(lista_compras=lista)
        self.assertFalse(gasto.is_paid())
        self.assertTrue(ListaCompras.objects.get(id=lista.id).is_done())
        self.assertRedirects(response, "/detalle_gasto/%d/" % (gasto.id))

        # old lista only has item_2
        self.assertEqual(lista.get_items().count(), 1)
        self.assertEqual(
            lista.get_items().first().item.nombre,
            item_lista_2.item.nombre)

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
                "options": "rescatar_items",
                "monto_total": 1000,
                str(item_lista_1.id): 1,
                str(item_lista_2.id): 2
            },
            follow=True)
        self.assertEqual(
            Gasto.objects.count(),
            original_gasto_count + 1)
        gasto = Gasto.objects.get(lista_compras=lista)
        self.assertFalse(gasto.is_paid())
        self.assertTrue(gasto.is_pending_confirm())
        self.assertTrue(ListaCompras.objects.get(id=lista.id).is_done())
        self.assertRedirects(response, "/detalle_gasto/%d/" % (gasto.id))

        # created new lista with item_2
        self.assertEqual(original_lista_count, ListaCompras.objects.count())
        # old lista only has both items, and is paid
        self.assertEqual(lista.get_items().count(), 2)

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
                "options": "rescatar_items",
                str(item_lista_1.id): 1,
                str(item_lista_2.id): 2
            },
            follow=True)
        self.assertRedirects(response, "/error/")
        self.assertEqual(ListaCompras.objects.count(), original_lista_count)
        self.assertEqual(Gasto.objects.count(), original_gasto_count)

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
                "options": "rescatar_items",
                "monto_total": 1000
            },
            follow=True)
        self.assertRedirects(response, "/error/")
        self.assertEqual(ListaCompras.objects.count(), original_lista_count)
        self.assertEqual(Gasto.objects.count(), original_gasto_count)


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
            "href=\"/presupuestos/%d/%d/%s/\">" % (
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
            "href=\"/presupuestos/%d/%d/%s/\">" % (
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
        Categoria.objects.create(nombre="asdf")
        my_cat = Categoria.objects.create(
            nombre="asdf",
            vivienda=test_user.get_vivienda())
        other_cat = Categoria.objects.create(
            nombre="asdf",
            vivienda=other_vivienda)
        my_presupuesto = Presupuesto.objects.create(
            categoria=my_cat,
            vivienda=test_user.get_vivienda(),
            monto=12345)
        url = "/presupuestos/%d/%d/%s/" % (
            my_presupuesto.year_month.year,
            my_presupuesto.year_month.month,
            my_presupuesto.categoria)

        other_presupuesto = Presupuesto.objects.create(
            categoria=other_cat,
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
        vivienda = test_user.get_vivienda()
        presupuesto = Presupuesto.objects.create(
            categoria=vivienda.get_categorias().first(),
            vivienda=vivienda,
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
        vivienda = test_user.get_vivienda()
        presupuesto = Presupuesto.objects.create(
            categoria=vivienda.get_categorias().first(),
            vivienda=vivienda,
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
        vivienda = test_user.get_vivienda()
        presupuesto = Presupuesto.objects.create(
            categoria=vivienda.get_categorias().first(),
            vivienda=vivienda,
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

    def test_user_can_see_own_disbalance(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(self)

        test_user_1.get_vu().confirm_pay(gasto_1)
        test_user_1.get_vu().confirm_pay(gasto_2)

        response = self.client.get(
            self.url,
            follow=True)

        expected_per_user = (gasto_1.monto + gasto_2.monto) / 2
        actual_total_user_1 = gasto_1.monto + gasto_2.monto
        actual_total_user_2 = 0

        balance_user_1 = actual_total_user_1 - expected_per_user
        balance_user_2 = actual_total_user_2 - expected_per_user

        # must cast to int because, in the template, decimals are separated
        # by commas instead of dots
        self.assertContains(response, int(balance_user_1))
        self.assertContains(response, int(balance_user_2))

    def test_user_can_see_disbalance_of_roommates(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(self)

        test_user_1.get_vu().confirm_pay(gasto_1)
        test_user_2.get_vu().confirm_pay(gasto_2)

        response = self.client.get(
            self.url,
            follow=True)

        expected_per_user = (gasto_1.monto + gasto_2.monto) / 2
        actual_total_user_1 = gasto_1.monto
        actual_total_user_2 = gasto_2.monto

        balance_user_1 = actual_total_user_1 - expected_per_user
        balance_user_2 = actual_total_user_2 - expected_per_user

        self.assertContains(response, int(balance_user_1))
        self.assertContains(response, int(balance_user_2))


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
        gasto_1.confirm_pay(test_user_1.get_vu())
        gasto_2.confirm_pay(test_user_1.get_vu())
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
        gasto_1.confirm_pay(test_user_1.get_vu())
        gasto_2.confirm_pay(test_user_1.get_vu())
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
                "unidad_medida": "kg"
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
                "unidad_medida": "kg"
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
                "unidad_medida": "kg"
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
                "unidad_medida": "kg"
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
        test_user = get_setup_with_gastos_items_and_listas(self)
        vivienda = test_user.get_vivienda()
        custom_item = Item.objects.create(
            nombre="customizimo",
            unidad_medida="kg",
            vivienda=vivienda)
        url = "/vivienda/item/%s/" % (custom_item.nombre)

        self.client.logout()
        response = self.client.post(
            url,
            data={
                "nombre": "new_name",
                "unidad_medida": "litros",
                "descripcion": "asdf"
            },
            follow=True)

        self.assertRedirects(
            response,
            "/accounts/login/?next=%s" % (url))
        self.assertEqual(
            Item.objects.get(id=custom_item.id).nombre,
            "customizimo")
        self.assertEqual(
            Item.objects.get(id=custom_item.id).unidad_medida,
            "kg")
        self.assertEqual(
            Item.objects.get(id=custom_item.id).descripcion,
            "")
        self.assertEqual(Item.objects.filter(
            nombre="customizimo",
            unidad_medida="kg",
            descripcion="",
            vivienda=vivienda).count(),
            1)

    def test_homeless_user_cant_edit_item(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        vivienda = test_user.get_vivienda()
        custom_item = Item.objects.create(
            nombre="customizimo",
            unidad_medida="kg",
            vivienda=vivienda)
        url = "/vivienda/item/%s/" % (custom_item.nombre)

        test_user.get_vu().leave()
        response = self.client.post(
            url,
            data={
                "nombre": "new_name",
                "unidad_medida": "litros",
                "descripcion": "asdf"
            },
            follow=True)

        self.assertRedirects(
            response,
            "/error/")
        self.assertContains(
            response,
            "Para tener acceso a esta página debe pertenecer a una vivienda")
        self.assertEqual(
            Item.objects.get(id=custom_item.id).nombre,
            "customizimo")
        self.assertEqual(
            Item.objects.get(id=custom_item.id).unidad_medida,
            "kg")
        self.assertEqual(
            Item.objects.get(id=custom_item.id).descripcion,
            "")
        self.assertEqual(Item.objects.filter(
            nombre="customizimo",
            unidad_medida="kg",
            descripcion="",
            vivienda=vivienda).count(),
            1)

    def test_user_cant_edit_item_of_other_vivienda(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        vivienda = test_user.get_vivienda()
        other_vivienda = Vivienda.objects.exclude(id=vivienda.id).first()
        custom_item = Item.objects.create(
            nombre="customizimo",
            unidad_medida="kg",
            vivienda=other_vivienda)
        url = "/vivienda/item/%s/" % (custom_item.nombre)

        response = self.client.post(
            url,
            data={
                "nombre": "new_name",
                "unidad_medida": "litros",
                "descripcion": "asdf"
            },
            follow=True)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            Item.objects.get(id=custom_item.id).nombre,
            "customizimo")
        self.assertEqual(
            Item.objects.get(id=custom_item.id).unidad_medida,
            "kg")
        self.assertEqual(
            Item.objects.get(id=custom_item.id).descripcion,
            "")
        self.assertEqual(Item.objects.filter(
            nombre="customizimo",
            unidad_medida="kg",
            descripcion="",
            vivienda=other_vivienda).count(),
            1)

    def test_user_can_edit_item_of_own_vivienda(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        vivienda = test_user.get_vivienda()
        other_vivienda = Vivienda.objects.exclude(id=vivienda.id).first()
        # both Viviendas just happened to create a custom item with the
        # same name
        my_custom_item = Item.objects.create(
            nombre="customizimo",
            unidad_medida="kg",
            vivienda=vivienda)
        others_custom_item = Item.objects.create(
            nombre="customizimo",
            unidad_medida="kg",
            vivienda=other_vivienda)
        url = "/vivienda/item/%s/" % (my_custom_item.nombre)

        response = self.client.post(
            url,
            data={
                "nombre": "new_name",
                "unidad_medida": "litros",
                "descripcion": "asdf"
            },
            follow=True)

        # only 'my_custom_item' should've been modified
        self.assertRedirects(response, "/vivienda/items/")
        self.assertEqual(
            Item.objects.get(id=my_custom_item.id).nombre,
            "new_name")
        self.assertEqual(
            Item.objects.get(id=my_custom_item.id).unidad_medida,
            "litros")
        self.assertEqual(
            Item.objects.get(id=my_custom_item.id).descripcion,
            "asdf")
        # 'others_custom_item' shouldn't have changed
        self.assertEqual(
            Item.objects.get(id=others_custom_item.id).nombre,
            "customizimo")
        self.assertEqual(
            Item.objects.get(id=others_custom_item.id).unidad_medida,
            "kg")
        self.assertEqual(
            Item.objects.get(id=others_custom_item.id).descripcion,
            "")

    def test_user_cant_edit_item_with_broken_POST(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        vivienda = test_user.get_vivienda()
        custom_item = Item.objects.create(
            nombre="customizimo",
            unidad_medida="kg",
            vivienda=vivienda)
        url = "/vivienda/item/%s/" % (custom_item.nombre)

        response = self.client.post(
            url,
            data={
                "nombre": "new_name",
                # "unidad_medida": "litros",
                "descripcion": "asdf"
            },
            follow=True)

        self.assertRedirects(response, url)
        self.assertContains(
            response,
            "Se produjo un error procesando la solicitud")
        self.assertEqual(
            Item.objects.get(id=custom_item.id).nombre,
            "customizimo")
        self.assertEqual(
            Item.objects.get(id=custom_item.id).unidad_medida,
            "kg")
        self.assertEqual(
            Item.objects.get(id=custom_item.id).descripcion,
            "")

        response = self.client.post(
            url,
            data={
                # "nombre": "new_name",
                "unidad_medida": "litros",
                "descripcion": "asdf"
            },
            follow=True)

        self.assertRedirects(response, url)
        self.assertContains(
            response,
            "Se produjo un error procesando la solicitud")
        self.assertEqual(
            Item.objects.get(id=custom_item.id).nombre,
            "customizimo")
        self.assertEqual(
            Item.objects.get(id=custom_item.id).unidad_medida,
            "kg")
        self.assertEqual(
            Item.objects.get(id=custom_item.id).descripcion,
            "")

        response = self.client.post(
            url,
            data={
                "nombre": "new_name",
                "unidad_medida": "litros"
                # "descripcion": "asdf"
            },
            follow=True)

        self.assertRedirects(response, "/vivienda/items/")
        self.assertEqual(
            Item.objects.get(id=custom_item.id).nombre,
            "new_name")
        self.assertEqual(
            Item.objects.get(id=custom_item.id).unidad_medida,
            "litros")
        self.assertEqual(
            Item.objects.get(id=custom_item.id).descripcion,
            "")


class UserIsOutListViewTest(TestCase):

    url = "/vivienda/vacaciones/"
    url_new = "/vivienda/vacaciones/new/"

    def test_not_logged_user_cant_see_vacation_list(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        self.client.logout()
        response = self.client.get(
            self.url,
            follow=True)

        self.assertRedirects(
            response,
            "/accounts/login/?next=%s" % (self.url))

    def test_homeless_user_cant_see_vacation_list(self):
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

    def test_user_can_see_link_to_new_vacation(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        response = self.client.get(
            self.url,
            follow=True)

        self.assertContains(
            response,
            self.url_new)

    def test_user_can_see_vacations_of_active_users_only(self):
        # create vivienda with 2 users
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(self)
        # create vacation for user
        vacation_1, __ = test_user_1.go_on_vacation()
        # create vacation for roommate
        vacation_2, __ = test_user_2.go_on_vacation(
            end_date=timezone.now().date() + timezone.timedelta(weeks=48))
        # roommate leaves
        test_user_2.leave()

        response = self.client.get(
            self.url,
            follow=True)

        self.assertContains(
            response,
            vacation_1.fecha_inicio.year)
        # month number doesn't appear, what apperas is "April"
        # self.assertContains(
        #     response,
        #     vacation_1.fecha_inicio.month)
        self.assertContains(
            response,
            vacation_1.fecha_inicio.day)
        self.assertContains(
            response,
            vacation_1.vivienda_usuario.user)

        self.assertNotContains(
            response,
            vacation_2.fecha_fin.year)
        self.assertNotContains(
            response,
            vacation_2.vivienda_usuario.user)

    def test_user_can_see_vacations_of_active_vivienda_only(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(self)
        today = timezone.now().date()
        # create vacations for old vivienda
        vacation_1, __ = test_user_1.go_on_vacation(
            end_date=today + timezone.timedelta(weeks=48))
        # 48 weeks ensure a 1-year difference
        # leave old vivienda
        test_user_1.leave()
        new_viv = Vivienda.objects.create(alias="newest_viv")
        new_user_viv = ViviendaUsuario.objects.create(
            user=test_user_1,
            vivienda=new_viv)
        # create vacation (diferent) for new vivienda
        vacation_2, __ = test_user_1.go_on_vacation(
            end_date=today + timezone.timedelta(weeks=2))

        self.assertEqual(test_user_1.get_vivienda().alias, "newest_viv")

        response = self.client.get(
            self.url,
            follow=True)

        self.assertContains(
            response,
            vacation_2.fecha_fin.year)
        self.assertContains(
            response,
            vacation_2.fecha_fin.day)
        self.assertNotContains(
            response,
            vacation_1.fecha_fin.year)

    def test_user_cant_see_vacations_of_other_vivienda(self):
        # create another vivienda with other users
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(self)
        today = timezone.now().date()
        # create vacations for other user
        other_vacation, __ = test_user_3.go_on_vacation(
            end_date=today + timezone.timedelta(weeks=48))
        # create vacations for this user
        this_vacation, __ = test_user_1.go_on_vacation(
            end_date=today + timezone.timedelta(weeks=2))

        response = self.client.get(
            self.url,
            follow=True)

        self.assertContains(
            response,
            this_vacation.fecha_fin.year)
        self.assertContains(
            response,
            this_vacation.fecha_fin.day)
        self.assertNotContains(
            response,
            other_vacation.fecha_fin.year)

    def test_user_can_see_link_to_edit_vacation(self):
        (test_user_1,
            test_user_2,
            test_user_3,
            dummy_categoria,
            gasto_1,
            gasto_2,
            gasto_3) = get_setup_viv_2_users_viv_1_user_cat_1_gastos_3(self)
        vacation, __ = test_user_1.go_on_vacation(
            end_date=timezone.now().date() + timezone.timedelta(weeks=4))

        response = self.client.get(
            self.url,
            follow=True)

        self.assertContains(
            response,
            "/vivienda/vacaciones/%d/" % (vacation.id))


class NewUserIsOutTest(TestCase):

    url = "/vivienda/vacaciones/new/"

    def test_not_logged_user_cant_create_vacation(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        start_date = timezone.now().date() + timezone.timedelta(weeks=4)
        end_date = timezone.now().date() + timezone.timedelta(weeks=10)

        self.client.logout()

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "fecha_inicio": start_date,
                "fecha_fin": end_date
            },
            follow=True)

        self.assertRedirects(
            response,
            "/accounts/login/?next=%s" % (self.url))

    def test_homeless_user_cant_create_vacation(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        start_date = timezone.now().date() + timezone.timedelta(weeks=4)
        end_date = timezone.now().date() + timezone.timedelta(weeks=10)

        test_user.get_vu().leave()

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "fecha_inicio": start_date,
                "fecha_fin": end_date
            },
            follow=True)

        self.assertRedirects(
            response,
            "/error/")
        self.assertContains(
            response,
            "Para tener acceso a esta página debe pertenecer a una vivienda")

    def test_user_can_create_vacation_without_start_nor_end_date_defined(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        self.assertFalse(UserIsOut.objects.filter(
            vivienda_usuario__user=test_user).exists())

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish"
            },
            follow=True)

        self.assertRedirects(
            response,
            "/vivienda/vacaciones/")
        self.assertTrue(UserIsOut.objects.filter(
            vivienda_usuario__user=test_user).exists())

    def test_user_can_create_vacation_with_defined_end_date_only(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        self.assertFalse(UserIsOut.objects.filter(
            vivienda_usuario__user=test_user).exists())

        end_date = timezone.now().date() + timezone.timedelta(weeks=4)

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "fecha_fin": end_date
            },
            follow=True)

        self.assertRedirects(
            response,
            "/vivienda/vacaciones/")
        self.assertTrue(UserIsOut.objects.filter(
            vivienda_usuario__user=test_user,
            fecha_fin=end_date).exists())

    def test_user_can_create_vacation_with_defined_start_date_only(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        self.assertFalse(UserIsOut.objects.filter(
            vivienda_usuario__user=test_user).exists())

        start_date = timezone.now().date() + timezone.timedelta(weeks=4)

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "fecha_inicio": start_date
            },
            follow=True)

        self.assertRedirects(
            response,
            "/vivienda/vacaciones/")
        self.assertTrue(UserIsOut.objects.filter(
            vivienda_usuario__user=test_user,
            fecha_inicio=start_date).exists())

    def test_user_can_create_vacation_with_defined_start_and_end_date(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        self.assertFalse(UserIsOut.objects.filter(
            vivienda_usuario__user=test_user).exists())

        start_date = timezone.now().date() + timezone.timedelta(weeks=4)
        end_date = timezone.now().date() + timezone.timedelta(weeks=10)

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "fecha_inicio": start_date,
                "fecha_fin": end_date
            },
            follow=True)

        self.assertRedirects(
            response,
            "/vivienda/vacaciones/")
        self.assertTrue(UserIsOut.objects.filter(
            vivienda_usuario__user=test_user,
            fecha_inicio=start_date,
            fecha_fin=end_date).exists())

    def test_user_cant_create_vacation_with_start_date_after_end_date(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        self.assertFalse(UserIsOut.objects.filter(
            vivienda_usuario__user=test_user).exists())

        start_date = timezone.now().date() + timezone.timedelta(weeks=10)
        end_date = timezone.now().date() + timezone.timedelta(weeks=4)

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "fecha_inicio": start_date,
                "fecha_fin": end_date
            },
            follow=True)

        self.assertRedirects(
            response,
            self.url)
        self.assertFalse(UserIsOut.objects.filter(
            vivienda_usuario__user=test_user).exists())
        self.assertContains(
            response,
            "La fecha final debe ser posterior a la fecha inicial.")

    def test_user_cant_create_vacation_that_overlaps_with_another(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        vacation_1, __ = test_user.go_on_vacation(
            start_date=timezone.now() + timezone.timedelta(weeks=1),
            end_date=timezone.now() + timezone.timedelta(weeks=4))

        today = timezone.now().date()
        # contained in vacation_1
        case1 = (today + timezone.timedelta(weeks=2),
                 today + timezone.timedelta(weeks=3))
        # contains vacation_1
        case2 = (today,
                 today + timezone.timedelta(weeks=5))
        # finishes too soon
        case3 = (today,
                 today + timezone.timedelta(weeks=3))
        # starts too late
        case4 = (today + timezone.timedelta(weeks=2),
                 today + timezone.timedelta(weeks=6))

        # dates that overlap with vacation_1
        for start_date, end_date in [case1, case2, case3, case4]:

            response = self.client.post(
                self.url,
                data={
                    "csrfmiddlewaretoken": "rubbish",
                    "fecha_inicio": start_date,
                    "fecha_fin": end_date
                },
                follow=True)

            self.assertRedirects(
                response,
                self.url)
            self.assertEqual(
                UserIsOut.objects.filter(
                    vivienda_usuario__user=test_user).count(),
                1)
            self.assertEqual(
                UserIsOut.objects.get(
                    vivienda_usuario__user=test_user).id,
                vacation_1.id)
            self.assertContains(
                response,
                "¡Las fechas indicadas topan con otra salida programada!")

    def test_user_cant_create_vacation_with_broken_POST(self):
        """
        Test that the user can't send a string that IS NOT a date in the post.
        Foe example, if the user sends "fecha_inicio":9999, it should show
        an error message and not create anything
        """
        test_user = get_setup_with_gastos_items_and_listas(self)

        self.assertFalse(UserIsOut.objects.filter(
            vivienda_usuario__user=test_user).exists())

        today = timezone.now().date()

        case1 = (today + timezone.timedelta(weeks=2),
                 9999)
        case2 = (9999,
                 today + timezone.timedelta(weeks=5))
        case3 = ("invalid_string",
                 today + timezone.timedelta(weeks=3))
        case4 = (today + timezone.timedelta(weeks=2),
                 "invalid_string")
        case5 = (9999,
                 "invalid_string")

        for start_date, end_date in [case1, case2, case3, case4, case5]:
            response = self.client.post(
                self.url,
                data={
                    "csrfmiddlewaretoken": "rubbish",
                    "fecha_inicio": start_date,
                    "fecha_fin": end_date
                },
                follow=True)
            self.assertRedirects(
                response,
                self.url)
            self.assertFalse(UserIsOut.objects.filter(
                vivienda_usuario__user=test_user).exists())
            self.assertContains(
                response,
                "Las fechas ingresadas no son válidas.")


class UserIsOutEditViewTest(TestCase):

    def test_not_logged_user_cant_edit_vacation(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        vacation, __ = test_user.go_on_vacation()
        url = "/vivienda/vacaciones/%d/" % (vacation.id)

        self.client.logout()

        start_date = timezone.now().date() + timezone.timedelta(weeks=1)
        end_date = timezone.now().date() + timezone.timedelta(weeks=3)

        response = self.client.post(
            url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "fecha_inicio": start_date,
                "fecha_fin": end_date
            },
            follow=True)

        self.assertRedirects(
            response,
            "/accounts/login/?next=%s" % (url))
        self.assertEqual(
            UserIsOut.objects.filter(
                vivienda_usuario__user=test_user).count(),
            1)
        self.assertEqual(
            UserIsOut.objects.get(id=vacation.id).fecha_fin,
            vacation.fecha_fin)
        self.assertNotEqual(
            UserIsOut.objects.get(id=vacation.id).fecha_fin,
            end_date)

    def test_homeless_user_cant_edit_vacation(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        vacation, __ = test_user.go_on_vacation()
        url = "/vivienda/vacaciones/%d/" % (vacation.id)

        test_user.get_vu().leave()

        start_date = timezone.now().date() + timezone.timedelta(weeks=1)
        end_date = timezone.now().date() + timezone.timedelta(weeks=3)

        response = self.client.post(
            url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "fecha_inicio": start_date,
                "fecha_fin": end_date
            },
            follow=True)

        self.assertRedirects(
            response,
            "/error/")
        self.assertContains(
            response,
            "Para tener acceso a esta página debe pertenecer a una vivienda")
        self.assertEqual(
            UserIsOut.objects.filter(
                vivienda_usuario__user=test_user).count(),
            1)
        self.assertEqual(
            UserIsOut.objects.get(id=vacation.id).fecha_fin,
            vacation.fecha_fin)
        self.assertNotEqual(
            UserIsOut.objects.get(id=vacation.id).fecha_fin,
            end_date)

    def test_user_can_edit_vacation_with_only_end_date(self):
        """
        The user can specify only a new end date. This should change the
        "fecha_fin" field, but not the "fecha_inicio" date! The latter field
        should stay the same, ie, not be changed to today.
        """
        test_user = get_setup_with_gastos_items_and_listas(self)
        vacation, __ = test_user.go_on_vacation()
        url = "/vivienda/vacaciones/%d/" % (vacation.id)

        end_date = timezone.now().date() + timezone.timedelta(weeks=3)

        response = self.client.post(
            url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "fecha_fin": end_date
            },
            follow=True)

        self.assertRedirects(response, "/vivienda/vacaciones/")
        self.assertEqual(
            UserIsOut.objects.filter(
                vivienda_usuario__user=test_user).count(),
            1)
        # "fecha_inicio" field did NOT change
        self.assertEqual(
            UserIsOut.objects.get(id=vacation.id).fecha_inicio,
            vacation.fecha_inicio)
        # "fecha_fin" field DID change
        self.assertNotEqual(
            UserIsOut.objects.get(id=vacation.id).fecha_fin,
            vacation.fecha_fin)
        self.assertEqual(
            UserIsOut.objects.get(id=vacation.id).fecha_fin,
            end_date)

    def test_user_can_edit_vacation_with_only_start_date(self):
        """
        The user can specify only a new start date. This should change the
        "fecha_inicio" field, but not the "fecha_fin" date! The latter field
        should stay the same, ie, not be changed to the year ~2200.
        """
        test_user = get_setup_with_gastos_items_and_listas(self)
        vacation, __ = test_user.go_on_vacation()
        url = "/vivienda/vacaciones/%d/" % (vacation.id)

        start_date = timezone.now().date() + timezone.timedelta(weeks=3)

        response = self.client.post(
            url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "fecha_inicio": start_date
            },
            follow=True)

        self.assertRedirects(response, "/vivienda/vacaciones/")
        self.assertEqual(
            UserIsOut.objects.filter(
                vivienda_usuario__user=test_user).count(),
            1)

        # "fecha_inicio" field DID change
        self.assertEqual(
            UserIsOut.objects.get(id=vacation.id).fecha_inicio,
            start_date)
        self.assertNotEqual(
            UserIsOut.objects.get(id=vacation.id).fecha_inicio,
            vacation.fecha_inicio)
        # "fecha_fin" field did NOT change
        self.assertEqual(
            UserIsOut.objects.get(id=vacation.id).fecha_fin,
            vacation.fecha_fin)

    def test_user_can_edit_vacation_with_both_start_and_end_date(self):
        """
        The user can specify both new dates in the POST request.
        """
        test_user = get_setup_with_gastos_items_and_listas(self)
        vacation, __ = test_user.go_on_vacation()
        url = "/vivienda/vacaciones/%d/" % (vacation.id)

        start_date = timezone.now().date() + timezone.timedelta(weeks=3)
        end_date = timezone.now().date() + timezone.timedelta(weeks=6)

        response = self.client.post(
            url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "fecha_inicio": start_date,
                "fecha_fin": end_date
            },
            follow=True)

        self.assertRedirects(response, "/vivienda/vacaciones/")
        self.assertEqual(
            UserIsOut.objects.filter(
                vivienda_usuario__user=test_user).count(),
            1)

        # "fecha_inicio" field changed
        self.assertEqual(
            UserIsOut.objects.get(id=vacation.id).fecha_inicio,
            start_date)
        self.assertNotEqual(
            UserIsOut.objects.get(id=vacation.id).fecha_inicio,
            vacation.fecha_inicio)
        # "fecha_fin" field changed
        self.assertEqual(
            UserIsOut.objects.get(id=vacation.id).fecha_fin,
            end_date)
        self.assertNotEqual(
            UserIsOut.objects.get(id=vacation.id).fecha_fin,
            vacation.fecha_fin)

    def test_user_cant_edit_vacation_without_giving_any_date(self):
        """
        The user shouldn't be able to edit a UserIsOut instance if
        he/she doesn't provide any dates. This would alter the UserIsOut's
        fields to the default values: (today - the year ~2200). This clearly
        isn't the desired behaviour!
        """
        test_user = get_setup_with_gastos_items_and_listas(self)
        start_date = timezone.now().date() + timezone.timedelta(weeks=3)
        end_date = timezone.now().date() + timezone.timedelta(weeks=6)
        vacation, __ = test_user.go_on_vacation(
            start_date=start_date,
            end_date=end_date)
        url = "/vivienda/vacaciones/%d/" % (vacation.id)

        response = self.client.post(
            url,
            data={
                "csrfmiddlewaretoken": "rubbish"
            },
            follow=True)

        self.assertRedirects(response, url)
        self.assertContains(
            response,
            "Debe especificar al menos una de las fechas.")
        self.assertEqual(
            UserIsOut.objects.filter(
                vivienda_usuario__user=test_user).count(),
            1)
        # neither field changed
        self.assertEqual(
            UserIsOut.objects.get(id=vacation.id).fecha_fin,
            vacation.fecha_fin)
        self.assertEqual(
            UserIsOut.objects.get(id=vacation.id).fecha_inicio,
            vacation.fecha_inicio)

    def test_user_cant_edit_vacation_if_vals_overlap_w_other_vacation(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        today = timezone.now().date()
        vacation_1, __ = test_user.go_on_vacation(
            start_date=today + timezone.timedelta(weeks=1),
            end_date=today + timezone.timedelta(weeks=4))
        vacation_2, __ = test_user.go_on_vacation(
            start_date=today + timezone.timedelta(weeks=6),
            end_date=today + timezone.timedelta(weeks=8))

        # contained in vacation_1
        case1 = (today + timezone.timedelta(weeks=2),
                 today + timezone.timedelta(weeks=3))
        # contains vacation_1
        case2 = (today,
                 today + timezone.timedelta(weeks=5))
        # finishes too soon
        case3 = (today,
                 today + timezone.timedelta(weeks=3))
        # starts too late
        case4 = (today + timezone.timedelta(weeks=2),
                 today + timezone.timedelta(weeks=6))

        url = "/vivienda/vacaciones/%d/" % (vacation_2.id)

        for start_date, end_date in [case1, case2, case3, case4]:

            response = self.client.post(
                url,
                data={
                    "csrfmiddlewaretoken": "rubbish",
                    "fecha_inicio": start_date,
                    "fecha_fin": end_date
                },
                follow=True)

            self.assertRedirects(
                response,
                url)
            self.assertEqual(
                UserIsOut.objects.filter(
                    vivienda_usuario__user=test_user).count(),
                2)
            # neither field changed
            self.assertEqual(
                UserIsOut.objects.get(id=vacation_2.id).fecha_fin,
                vacation_2.fecha_fin)
            self.assertEqual(
                UserIsOut.objects.get(id=vacation_2.id).fecha_inicio,
                vacation_2.fecha_inicio)
            self.assertContains(
                response,
                "¡Las fechas indicadas topan con otra salida programada!")

    def test_user_cant_edit_vacation_if_start_date_after_end_date(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        vacation, __ = test_user.go_on_vacation()
        url = "/vivienda/vacaciones/%d/" % (vacation.id)

        start_date = timezone.now().date() + timezone.timedelta(weeks=6)
        end_date = timezone.now().date() + timezone.timedelta(weeks=3)

        response = self.client.post(
            url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "fecha_inicio": start_date,
                "fecha_fin": end_date
            },
            follow=True)

        self.assertRedirects(response, url)
        self.assertEqual(
            UserIsOut.objects.filter(
                vivienda_usuario__user=test_user).count(),
            1)
        # neither field changed
        self.assertEqual(
            UserIsOut.objects.get(id=vacation.id).fecha_fin,
            vacation.fecha_fin)
        self.assertEqual(
            UserIsOut.objects.get(id=vacation.id).fecha_inicio,
            vacation.fecha_inicio)
        self.assertContains(
            response,
            "La fecha final debe ser posterior a la fecha inicial.")

    def test_user_cant_edit_other_users_vacation(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        other_user = ProxyUser.objects.get(username="test_user_3")
        other_vacation, __ = other_user.go_on_vacation()
        url = "/vivienda/vacaciones/%d/" % (other_vacation.id)

        start_date = timezone.now().date() + timezone.timedelta(weeks=6)
        end_date = timezone.now().date() + timezone.timedelta(weeks=3)

        response = self.client.post(
            url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "fecha_inicio": start_date,
                "fecha_fin": end_date
            },
            follow=True)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            UserIsOut.objects.filter(
                vivienda_usuario__user=other_user).count(),
            1)
        self.assertEqual(
            UserIsOut.objects.filter(
                vivienda_usuario__user=test_user).count(),
            0)
        # neither field changed
        self.assertEqual(
            UserIsOut.objects.get(id=other_vacation.id).fecha_fin,
            other_vacation.fecha_fin)
        self.assertEqual(
            UserIsOut.objects.get(id=other_vacation.id).fecha_inicio,
            other_vacation.fecha_inicio)

    def test_user_cant_edit_roommates_vacation(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        roommate = ProxyUser.objects.get(username="test_user_2")
        roommate_vacation, __ = roommate.go_on_vacation()
        url = "/vivienda/vacaciones/%d/" % (roommate_vacation.id)

        start_date = timezone.now().date() + timezone.timedelta(weeks=6)
        end_date = timezone.now().date() + timezone.timedelta(weeks=3)

        response = self.client.post(
            url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "fecha_inicio": start_date,
                "fecha_fin": end_date
            },
            follow=True)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            UserIsOut.objects.filter(
                vivienda_usuario__user=roommate).count(),
            1)
        self.assertEqual(
            UserIsOut.objects.filter(
                vivienda_usuario__user=test_user).count(),
            0)
        # neither field changed
        self.assertEqual(
            UserIsOut.objects.get(id=roommate_vacation.id).fecha_fin,
            roommate_vacation.fecha_fin)
        self.assertEqual(
            UserIsOut.objects.get(id=roommate_vacation.id).fecha_inicio,
            roommate_vacation.fecha_inicio)


class NewTransferViewTest(TestCase):

    url = "/transfer/"

    def test_not_logged_user_cant_create_transfer(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        roommate = ProxyUser.objects.get(username="test_user_2")

        self.client.logout()

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "user": roommate.id,
                "monto": 10000
            },
            follow=True)

        self.assertRedirects(
            response,
            "/accounts/login/?next=%s" % (self.url))
        self.assertEqual(Gasto.objects.count(), 3)

    def test_cant_transfer_to_homeless(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        roommate = ProxyUser.objects.get(username="test_user_2")

        roommate.leave()

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "user": roommate.id,
                "monto": 10000
            },
            follow=True)

        self.assertRedirects(
            response,
            self.url)
        self.assertContains(
            response,
            "El usuario indicado no pertenece a su Vivienda.")
        self.assertEqual(Gasto.objects.count(), 3)

    def test_homeless_cant_transfer(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        roommate = ProxyUser.objects.get(username="test_user_2")

        test_user.leave()

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "user": roommate.id,
                "monto": 10000
            },
            follow=True)

        self.assertRedirects(
            response,
            "/error/")
        self.assertContains(
            response,
            "Para tener acceso a esta página debe pertenecer a una vivienda")
        self.assertEqual(Gasto.objects.count(), 3)

    def test_homeless_cant_transfer_to_homeless(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        roommate = ProxyUser.objects.get(username="test_user_2")

        test_user.leave()
        roommate.leave()

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "user": roommate.id,
                "monto": 10000
            },
            follow=True)

        self.assertRedirects(
            response,
            "/error/")
        self.assertContains(
            response,
            "Para tener acceso a esta página debe pertenecer a una vivienda")
        self.assertEqual(Gasto.objects.count(), 3)

    def test_transfer_monto_must_be_positive_integer(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        roommate = ProxyUser.objects.get(username="test_user_2")

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "user": roommate.id,
                "monto": -10000
            },
            follow=True)

        self.assertRedirects(
            response,
            self.url)
        self.assertContains(
            response,
            "Debe ingresar un monto mayor que 0.")
        self.assertEqual(Gasto.objects.count(), 3)

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "user": roommate.id,
                "monto": 0
            },
            follow=True)

        self.assertRedirects(
            response,
            self.url)
        self.assertContains(
            response,
            "Debe ingresar un monto mayor que 0.")
        self.assertEqual(Gasto.objects.count(), 3)

    def test_cant_transfer_with_broken_POST(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        roommate = ProxyUser.objects.get(username="test_user_2")

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "monto": 10000
            },
            follow=True)

        self.assertRedirects(
            response,
            self.url)
        self.assertContains(
            response,
            "Debe especificar un usuario a quien transferirle.")
        self.assertEqual(Gasto.objects.count(), 3)

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "user": "",
                "monto": 10000
            },
            follow=True)

        self.assertRedirects(
            response,
            self.url)
        self.assertContains(
            response,
            "Debe especificar un usuario a quien transferirle.")
        self.assertEqual(Gasto.objects.count(), 3)

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "user": roommate.id
            },
            follow=True)

        self.assertRedirects(
            response,
            self.url)
        self.assertContains(
            response,
            "Debe ingresar un monto mayor que 0.")
        self.assertEqual(Gasto.objects.count(), 3)

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "user": roommate.id,
                "monto": ""
            },
            follow=True)

        self.assertRedirects(
            response,
            self.url)
        self.assertContains(
            response,
            "Debe ingresar un monto mayor que 0.")
        self.assertEqual(Gasto.objects.count(), 3)

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish"
            },
            follow=True)

        self.assertRedirects(
            response,
            self.url)
        self.assertContains(
            response,
            "Debe especificar un usuario a quien transferirle.")
        self.assertEqual(Gasto.objects.count(), 3)

    def test_cant_transfer_to_self(self):
        test_user = get_setup_with_gastos_items_and_listas(self)

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "user": test_user.id,
                "monto": 10000
            },
            follow=True)

        self.assertRedirects(
            response,
            self.url)
        self.assertContains(
            response,
            "¡No puede transferirse fondos a sí mismo!")
        self.assertEqual(Gasto.objects.count(), 3)

    def test_logged_user_w_vivivenda_can_transfer_to_roommate(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        roommate = ProxyUser.objects.get(username="test_user_2")

        response = self.client.post(
            self.url,
            data={
                "csrfmiddlewaretoken": "rubbish",
                "user": roommate.id,
                "monto": 10000
            },
            follow=True)

        self.assertRedirects(
            response,
            "/vivienda/balance/")
        self.assertContains(
            response,
            "Transferencia realizada con éxito.")
        # assert that the new Gastos' states are not paid, but pending_confirm
        self.assertEqual(Gasto.objects.count(), 5)
