# -*- coding: utf-8 -*-
from django.test import TestCase
from expenses_manager.helper_functions.tests import *


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
        user1_viv.confirm_pay(gasto)
        self.assertFalse(gasto.is_pending())
        self.assertTrue(gasto.is_paid())
        self.assertTrue(gasto.allow_user(user1))

    def test_user_can_leave_with_finite_period(self):
        (user1,
         user2,
         correct_vivienda,
         user1_viv,
         user2_viv) = get_vivienda_with_2_users()

        self.assertFalse(user1.is_out())
        self.assertFalse(user2.is_out())

        user1.go_on_vacation(
            end_date=timezone.now().date() + timezone.timedelta(weeks=2))

        self.assertTrue(user1.is_out())
        self.assertFalse(user2.is_out())

    def test_user_can_leave_with_no_end_date(self):
        (user1,
         user2,
         correct_vivienda,
         user1_viv,
         user2_viv) = get_vivienda_with_2_users()

        self.assertFalse(user1.is_out())
        self.assertFalse(user2.is_out())

        user1.go_on_vacation()

        self.assertTrue(user1.is_out())
        self.assertFalse(user2.is_out())

    def test_method_leave(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()

        self.assertTrue(ViviendaUsuario.objects.get(
            user=user1,
            vivienda=correct_vivienda).is_active())

        user1.leave()

        self.assertFalse(ViviendaUsuario.objects.get(
            user=user1,
            vivienda=correct_vivienda).is_active())
        self.assertEqual(
            ViviendaUsuario.objects.filter(
                vivienda=correct_vivienda,
                estado="activo").count(),
            0)

    def test_method_transfer(self):
        # create vivienda with 3 users
        (user1,
         user2,
         vivienda,
         user1_viv,
         user2_viv) = get_vivienda_with_2_users()
        user3 = ProxyUser.objects.create(username="us3", email="c@c.com")
        user3_viv = ViviendaUsuario.objects.create(
            vivienda=vivienda, user=user3)
        # create 2 categorias A, B
        cat_1 = Categoria.objects.create(
            nombre="cat_1",
            vivienda=vivienda)
        cat_2 = Categoria.objects.create(
            nombre="cat_2",
            vivienda=vivienda)
        # create 2 periods P1, P2
        date1 = timezone.now().date() + timezone.timedelta(weeks=8)
        date2 = timezone.now().date() + timezone.timedelta(weeks=16)
        p1 = YearMonth.objects.create(year=date1.year, month=date1.month)
        p2 = YearMonth.objects.create(year=date2.year, month=date2.month)
        # create 2 gastos per user, using different combinations
        # of A,B and P1, P2
        estado_pagado = EstadoGasto.objects.create(estado="pagado")
        # gastos user1
        g1_1 = Gasto.objects.create(
            monto=1000,
            creado_por=user1.get_vu(),
            categoria=cat_1)
        user1_viv.confirm_pay(g1_1, date1)
        g1_2 = Gasto.objects.create(
            monto=2000,
            creado_por=user1.get_vu(),
            categoria=cat_2)
        user1_viv.confirm_pay(g1_2, date1)
        # gastos user2
        g2_1 = Gasto.objects.create(
            monto=500,
            creado_por=user2.get_vu(),
            categoria=cat_1)
        user2_viv.confirm_pay(g2_1, date1)
        g2_2 = Gasto.objects.create(
            monto=1700,
            creado_por=user2.get_vu(),
            categoria=cat_2)
        user2_viv.confirm_pay(g2_2, date2)
        # gastos user3
        g3_1 = Gasto.objects.create(
            monto=1200,
            creado_por=user3.get_vu(),
            categoria=cat_1)
        user3_viv.confirm_pay(g3_1, date1)
        g3_2 = Gasto.objects.create(
            monto=700,
            creado_por=user3.get_vu(),
            categoria=cat_1)
        user3_viv.confirm_pay(g3_2, date1)

        # create presupuesto for each categoria
        presupuesto_1_p1 = Presupuesto.objects.create(
            categoria=cat_1,
            vivienda=vivienda,
            year_month=p1,
            monto=5000)
        presupuesto_1_p2 = Presupuesto.objects.create(
            categoria=cat_1,
            vivienda=vivienda,
            year_month=p2,
            monto=6000)
        presupuesto_2_p1 = Presupuesto.objects.create(
            categoria=cat_2,
            vivienda=vivienda,
            year_month=p1,
            monto=4500)
        presupuesto_2_p2 = Presupuesto.objects.create(
            categoria=cat_2,
            vivienda=vivienda,
            year_month=p2,
            monto=4000)

        # get total so far for each presupuesto
        total_presupuesto_1_p1 = presupuesto_1_p1.get_total_expenses()
        total_presupuesto_1_p2 = presupuesto_1_p2.get_total_expenses()
        total_presupuesto_2_p1 = presupuesto_2_p1.get_total_expenses()
        total_presupuesto_2_p2 = presupuesto_2_p2.get_total_expenses()
        # get total_per_user
        total_per_user, __ = vivienda.get_smart_totals()
        # get total_per_period
        total_p1 = vivienda.get_total_expenses_period(p1)
        total_p2 = vivienda.get_total_expenses_period(p2)
        # get total_per_categoria_per_period
        # cat_1
        total_ca1_p1 = vivienda.get_total_expenses_categoria_period(cat_1, p1)
        total_ca1_p2 = vivienda.get_total_expenses_categoria_period(cat_1, p2)
        # cat_2
        total_ca2_p1 = vivienda.get_total_expenses_categoria_period(cat_2, p1)
        total_ca2_p2 = vivienda.get_total_expenses_categoria_period(cat_2, p2)

        self.assertEqual(Gasto.objects.count(), 6)

        # user1 should have 3000 total
        self.assertEqual(total_per_user[user1_viv], 3000)
        # user2 should have 2200 total
        self.assertEqual(total_per_user[user2_viv], 2200)
        # user3 should have 1900 total
        self.assertEqual(total_per_user[user3_viv], 1900)

        # TRANSFER METHOD CALL!!
        # user1 has spent way too much money! He can't even buy lunch anymore!
        # let's have user2 transfer him some money to balance things up a bit
        transfer_pos, transfer_neg = user2.transfer(user1, 400)
        # confirms all transfers
        user1_viv.confirm(transfer_pos)
        user2_viv.confirm(transfer_pos)
        user3_viv.confirm(transfer_pos)

        user1_viv.confirm(transfer_neg)
        user2_viv.confirm(transfer_neg)
        user3_viv.confirm(transfer_neg)

        # there are 2 new Gastos
        self.assertEqual(Gasto.objects.count(), 8)
        # the new Gastos' categoria is "Transferencia"
        self.assertEqual(transfer_pos.categoria.nombre, "Transferencia")
        self.assertEqual(transfer_neg.categoria.nombre, "Transferencia")
        # both new Gastos' monto's absolute value is 400
        self.assertEqual(abs(transfer_pos.monto), 400)
        self.assertEqual(abs(transfer_neg.monto), 400)
        # transfer_pos's monto is positive, and transfer_neg is negative
        self.assertTrue(transfer_pos.monto > 0)
        self.assertTrue(transfer_neg.monto < 0)

        # total_per_period did NOT change
        self.assertEqual(total_p1, vivienda.get_total_expenses_period(p1))
        self.assertEqual(total_p2, vivienda.get_total_expenses_period(p2))

        # total_per_categoria_per_period did NOT change
        # cat_1
        self.assertEqual(
            total_ca1_p1,
            vivienda.get_total_expenses_categoria_period(cat_1, p1))
        self.assertEqual(
            total_ca1_p2,
            vivienda.get_total_expenses_categoria_period(cat_1, p2))
        # cat_2
        self.assertEqual(
            total_ca2_p1,
            vivienda.get_total_expenses_categoria_period(cat_2, p1))
        self.assertEqual(
            total_ca2_p2,
            vivienda.get_total_expenses_categoria_period(cat_2, p2))

        # total_per_user DID change
        new_total_per_user, __ = vivienda.get_smart_totals()
        # user1 should now have 2600 total
        self.assertNotEqual(
            total_per_user[user1_viv],
            new_total_per_user[user1_viv])
        self.assertEqual(new_total_per_user[user1_viv], 2600)
        # user2 should now have 2600 total
        self.assertNotEqual(
            total_per_user[user2_viv],
            new_total_per_user[user2_viv])
        self.assertEqual(new_total_per_user[user2_viv], 2600)
        # user3 should still have 1900 total
        self.assertEqual(
            total_per_user[user3_viv],
            new_total_per_user[user3_viv])
        self.assertEqual(new_total_per_user[user3_viv], 1900)

        # the total of presupuestos did NOT change
        self.assertEqual(
            total_presupuesto_1_p1,
            presupuesto_1_p1.get_total_expenses())
        self.assertEqual(
            total_presupuesto_1_p2,
            presupuesto_1_p2.get_total_expenses())
        self.assertEqual(
            total_presupuesto_2_p1,
            presupuesto_2_p1.get_total_expenses())
        self.assertEqual(
            total_presupuesto_2_p2,
            presupuesto_2_p2.get_total_expenses())

        # the sum of each total_per_user is the SAME as the original sum of
        # each total_per_user
        original_sum = sum([v for k, v in total_per_user.items()])
        new_sum = sum([v for k, v in new_total_per_user.items()])
        self.assertEqual(original_sum, new_sum)

    def test_user_cant_transfer_to_himself(self):
        (user1,
         user2,
         vivienda,
         user1_viv,
         user2_viv) = get_vivienda_with_2_users()

        self.assertEqual(Gasto.objects.count(), 0)

        transfer_pos, transfer_neg = user1.transfer(user1, 10000)

        self.assertEqual(Gasto.objects.count(), 0)
        self.assertEqual(transfer_pos, None)
        self.assertEqual(transfer_neg, None)

    def test_user_cant_transfer_to_non_roommate(self):
        (user1,
         user2,
         vivienda,
         user1_viv,
         user2_viv) = get_vivienda_with_2_users()

        user1_viv.leave()

        transfer_pos, transfer_neg = user2.transfer(user1, 10000)

        self.assertEqual(Gasto.objects.count(), 0)
        self.assertEqual(transfer_pos, None)
        self.assertEqual(transfer_neg, None)

    def test_homeless_user_cant_transfer(self):
        (user1,
         user2,
         vivienda,
         user1_viv,
         user2_viv) = get_vivienda_with_2_users()

        user1_viv.leave()

        transfer_pos, transfer_neg = user1.transfer(user2, 10000)

        self.assertEqual(Gasto.objects.count(), 0)
        self.assertEqual(transfer_pos, None)
        self.assertEqual(transfer_neg, None)

    def test_homeless_user_cant_transfer_to_homeless(self):
        (user1,
         user2,
         vivienda,
         user1_viv,
         user2_viv) = get_vivienda_with_2_users()

        user1_viv.leave()
        user2_viv.leave()

        transfer_pos, transfer_neg = user1.transfer(user2, 10000)

        self.assertEqual(Gasto.objects.count(), 0)
        self.assertEqual(transfer_pos, None)
        self.assertEqual(transfer_neg, None)

    def test_transfer_monto_must_be_positive_integer(self):
        (user1,
         user2,
         vivienda,
         user1_viv,
         user2_viv) = get_vivienda_with_2_users()

        transfer_pos, transfer_neg = user1.transfer(user2, -1000)

        self.assertEqual(Gasto.objects.count(), 0)
        self.assertEqual(transfer_pos, None)
        self.assertEqual(transfer_neg, None)

        transfer_pos, transfer_neg = user1.transfer(user2, 0)

        self.assertEqual(Gasto.objects.count(), 0)
        self.assertEqual(transfer_pos, None)
        self.assertEqual(transfer_neg, None)


class ViviendaModelTest(TestCase):

    def test_get_gastos_from_vivienda_without_gastos(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()

        gastos_pendientes_direct = correct_vivienda.get_gastos_pendientes()
        gastos_pagados_direct = correct_vivienda.get_gastos_pagados()
        gastos_pendientes = correct_vivienda.get_gastos_pendientes()
        gastos_pagados = correct_vivienda.get_gastos_pagados()

        self.assertEqual(gastos_pendientes.count(), 0)
        self.assertEqual(gastos_pagados.count(), 0)
        self.assertEqual(gastos_pendientes_direct.count(), 0)
        self.assertEqual(gastos_pagados_direct.count(), 0)

    def test_get_gastos_from_vivienda_with_gastos_pendientes(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        gasto, dummy_categoria = get_dummy_gasto_pendiente(user1_viv)

        gastos_pendientes_direct = correct_vivienda.get_gastos_pendientes()
        gastos_pagados_direct = correct_vivienda.get_gastos_pagados()
        gastos_pendientes = correct_vivienda.get_gastos_pendientes()
        gastos_pagados = correct_vivienda.get_gastos_pagados()

        self.assertEqual(gastos_pendientes.count(), 1)
        self.assertEqual(gastos_pagados.count(), 0)
        self.assertEqual(gastos_pendientes_direct.count(), 1)
        self.assertEqual(gastos_pagados_direct.count(), 0)

    def test_get_gastos_from_vivienda_with_gastos_pagados(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        gasto, dummy_categoria = get_dummy_gasto_pendiente(user1_viv)
        user1_viv.confirm_pay(gasto)

        gastos_pendientes_direct = correct_vivienda.get_gastos_pendientes()
        gastos_pagados_direct = correct_vivienda.get_gastos_pagados()
        gastos_pendientes = correct_vivienda.get_gastos_pendientes()
        gastos_pagados = correct_vivienda.get_gastos_pagados()

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

    def test_get_items(self):
        test_user = get_setup_with_gastos_items_and_listas(self)
        vivienda = test_user.get_vivienda()
        custom_item = Item.objects.create(
            nombre="customizimo",
            vivienda=vivienda)

        self.assertEqual(vivienda.get_items().count(), 4)
        for item in vivienda.get_items():
            self.assertEqual(item.vivienda, vivienda)

        other_vivienda = Vivienda.objects.exclude(id=vivienda.id).first()
        self.assertEqual(other_vivienda.get_items().count(), 3)
        for item in other_vivienda.get_items():
            self.assertNotEqual(item.vivienda, vivienda)

    def test_get_total_expenses_per_active_user_with_vacations(self):
        db = get_setup_w_vivienda_3_users_and_periods()
        # user1 is out from period B-D
        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]

        user1_viv = db["user1_viv"]
        user2_viv = db["user2_viv"]
        user3_viv = db["user3_viv"]

        vivienda = db["vivienda"]

        user1.go_on_vacation(start_date=db["pB"], end_date=db["pD"])
        # user3 is out from period C-E
        user3.go_on_vacation(start_date=db["pC"], end_date=db["pE"])

        # Gnsl1 = user1 makes gasto cat_not_shared_on_leave on A for 1200
        gnsl1 = Gasto.objects.create(
            monto=1200,
            creado_por=user1.get_vu(),
            categoria=db["cat_not_shared_on_leave"])
        user1_viv.confirm_pay(gnsl1, fecha_pago=db["pA"])
        # Gnsl2 = user2 makes gasto cat_not_shared_on_leave on C for 2000
        gnsl2 = Gasto.objects.create(
            monto=2000,
            creado_por=user2.get_vu(),
            categoria=db["cat_not_shared_on_leave"])
        user2_viv.confirm_pay(gnsl2, fecha_pago=db["pC"])
        # Gsl1 = user3 makes gasto cat_shared_on_leave on B for 1500
        gsl1 = Gasto.objects.create(
            monto=1500,
            creado_por=user3.get_vu(),
            categoria=db["cat_shared_on_leave"])
        user3_viv.confirm_pay(gsl1, fecha_pago=db["pB"])
        # periods  :    A   |    B   | C
        # gastos   :  gnsl1 |  gsl1  | gnsl2
        # users out:  none  |  user1 | (user1, user3)
        # gnsl1 should be payed by: all => +400 each
        # gsl1 should be payed by: all => +500 each
        # gnsl2 should be payed by: user2 => +2000 user2
        # users have payed: {user1:1200, user2: 2000, user3: 1500}

        active_users = {user1_viv, user2_viv, user3_viv}
        all_users = {user1_viv, user2_viv, user3_viv}

        vacations = vivienda.get_vacations_after_date(db["pA"])

        gastos_users_dict = vivienda.get_smart_gasto_dict(
            active_users,
            all_users,
            vacations)

        (__, expected_per_user) = vivienda.get_reversed_user_totals_dict(
            gastos_users_dict)

        # users SHOULD have payed:
        # {
        #   user1_viv:900,
        #   user2_viv: 2900,
        #   user3_viv: 900
        # }
        self.assertEqual(expected_per_user.get(user1_viv, None), 900)
        self.assertEqual(expected_per_user.get(user2_viv, None), 2900)
        self.assertEqual(expected_per_user.get(user3_viv, None), 900)

    def test_get_vacations_after_date_method(self):
        """
        Tests that the method get_vacations_after_date(date) returns all
        vacations that happened after the given date for users of
        this Vivienda
        """
        db = get_setup_w_vivienda_3_users_and_periods()
        # user1 is out from period B-D
        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        vivienda = db["vivienda"]
        user1.go_on_vacation(start_date=db["pA"], end_date=db["pC"])
        user2.go_on_vacation(start_date=db["pA"], end_date=db["pB"])
        user3.go_on_vacation(start_date=db["pC"], end_date=db["pE"])

        user2_viv = user2.get_vu()
        user2_viv.fecha_creacion = db["pA"]
        user2_viv.fecha_abandono = db["pC"]
        user2_viv.estado = "inactivo"
        user2_viv.save()

        vacations_a = vivienda.get_vacations_after_date(db["pA"])
        self.assertEqual(len(vacations_a), 3)

        vacations_b = vivienda.get_vacations_after_date(db["pB"])
        self.assertEqual(len(vacations_b), 3)

        vacations_c = vivienda.get_vacations_after_date(db["pC"])
        self.assertEqual(len(vacations_c), 2)

        vacations_d = vivienda.get_vacations_after_date(db["pD"])
        self.assertEqual(len(vacations_d), 1)
        self.assertEqual(
            vacations_d.first().vivienda_usuario.user,
            user3)

        vacations_e = vivienda.get_vacations_after_date(db["pE"])
        self.assertEqual(len(vacations_e), 1)
        self.assertEqual(
            vacations_e.first().vivienda_usuario.user,
            user3)

        vacations_f = vivienda.get_vacations_after_date(db["pF"])
        self.assertEqual(len(vacations_f), 0)

    def test_get_smart_gasto_dict_method_no_left_no_vacation(self):
        db = get_setup_w_vivienda_3_users_and_periods()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user1_viv = user1.get_vu()
        user3_viv = user3.get_vu()
        user2_viv = user2.get_vu()
        vivienda = db["vivienda"]

        all_users = {user1_viv, user2_viv, user3_viv}

        cat_shared_on_leave = db["cat_shared_on_leave"]

        gasto_1 = Gasto.objects.create(
            monto=1200,
            creado_por=user1_viv,
            categoria=cat_shared_on_leave)
        user1_viv.confirm_pay(gasto_1, fecha_pago=db["pB"])

        gasto_2 = Gasto.objects.create(
            monto=3000,
            creado_por=user2_viv,
            categoria=cat_shared_on_leave)
        user2_viv.confirm_pay(gasto_2, fecha_pago=db["pD"])

        gasto_user_dict = vivienda.get_smart_gasto_dict(
            active_users=all_users,
            all_users=all_users,
            vacations=dict())

        self.assertEqual(gasto_user_dict[gasto_1], (all_users, all_users))
        self.assertEqual(gasto_user_dict[gasto_2], (all_users, all_users))

    def test_get_smart_gasto_dict_method_no_left_w_vacation(self):
        db = get_setup_w_vivienda_3_users_and_periods()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user1_viv = user1.get_vu()
        user3_viv = user3.get_vu()
        user2_viv = user2.get_vu()
        vivienda = db["vivienda"]

        vac2, __ = user2.go_on_vacation(start_date=db["pB"], end_date=db["pD"])

        vacations = [vac2]

        all_users = {user1_viv, user2_viv, user3_viv}

        cat_not_shared_on_leave = db["cat_not_shared_on_leave"]
        cat_shared_on_leave = db["cat_shared_on_leave"]

        gasto_1 = Gasto.objects.create(
            monto=1200,
            creado_por=user1_viv,
            categoria=cat_shared_on_leave)
        user1_viv.confirm_pay(gasto_1, fecha_pago=db["pB"])

        gasto_2 = Gasto.objects.create(
            monto=3000,
            creado_por=user3_viv,
            categoria=cat_not_shared_on_leave)
        user3_viv.confirm_pay(gasto_2, fecha_pago=db["pD"])

        gasto_user_dict = vivienda.get_smart_gasto_dict(
            active_users=all_users,
            all_users=all_users,
            vacations=vacations)

        self.assertEqual(gasto_user_dict[gasto_1], (all_users, all_users))
        self.assertEqual(
            gasto_user_dict[gasto_2],
            ({user1_viv, user3_viv},
             {user1_viv, user3_viv})
        )

    def test_get_smart_gasto_dict_method_w_left_w_vacation(self):
        db = get_setup_w_vivienda_3_users_and_periods()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user1_viv = user1.get_vu()
        user3_viv = user3.get_vu()
        user2_viv = user2.get_vu()
        vivienda = db["vivienda"]

        user2_viv.fecha_abandono = db["pC"]
        user2_viv.estado = "inactivo"

        user3_viv.fecha_creacion = db["pC"]

        vac1, __ = user1.go_on_vacation(start_date=db["pB"], end_date=db["pC"])
        vac3, __ = user3.go_on_vacation(start_date=db["pE"])
        vacations = {vac1, vac3}

        cat_not_shared_on_leave = db["cat_not_shared_on_leave"]
        cat_shared_on_leave = db["cat_shared_on_leave"]

        gasto_1 = Gasto.objects.create(
            monto=1200,
            creado_por=user2_viv,
            categoria=cat_not_shared_on_leave)
        user2_viv.confirm_pay(gasto_1, fecha_pago=db["pB"])

        gasto_2 = Gasto.objects.create(
            monto=1500,
            creado_por=user3_viv,
            categoria=cat_shared_on_leave)
        user3_viv.confirm_pay(gasto_2, fecha_pago=db["pC"])

        gasto_3 = Gasto.objects.create(
            monto=2000,
            creado_por=user1_viv,
            categoria=cat_shared_on_leave)
        user1_viv.confirm_pay(gasto_3, fecha_pago=db["pE"])

        # save so that the fields are actually modified
        user2_viv.save()
        user3_viv.save()

        all_users = {user1_viv, user2_viv, user3_viv}

        gasto_user_dict = vivienda.get_smart_gasto_dict(
            active_users={user1_viv, user3_viv},
            all_users=all_users,
            vacations=vacations)

        self.assertEqual(gasto_user_dict.get(gasto_1, None), None)
        self.assertEqual(
            gasto_user_dict[gasto_2],
            ({user1_viv, user3_viv},
             all_users))
        self.assertEqual(
            gasto_user_dict[gasto_3],
            ({user1_viv, user3_viv},
             {user1_viv, user3_viv})
        )

    def test_get_smart_gasto_dict_method_hard(self):
        """
        Tests that the method get_smart_gasto_dict returns the correct
        dict given a set of active_users and a set of vacations. This dict
        is of the form:
        {
            Gasto: (
                currently_active_users_that_should_pay_this_Gasto,
                users_active_at_the_time_of_Gasto_that_had_to_pay_it
            )
        }
        The keys are Gasto instances payed by Users that are currently active,
        and the values are tuples of Sets. Note that these Sets:
        - don't necessarily contain the same set of Users
        - are not necessarily of the same length
        - always have at least 1 user in common (the one who payed the Gasto)
        """
        db = get_hard_balance_test_database()

        user1_viv = db["user1_viv"]
        user2_viv = db["user2_viv"]
        user3_viv = db["user3_viv"]
        vivienda = db["vivienda"]

        active_users = {user1_viv, user3_viv}
        all_users = {user1_viv, user2_viv, user3_viv}

        vacations = vivienda.get_vacations_after_date(db["pA"])
        gastos_users_dict = vivienda.get_smart_gasto_dict(
            active_users,
            all_users,
            vacations)

        # the resulting dict should look like this (with Gasto
        # instances instead of ids as keys):
        # {
        #   1 : ({user1}, {user2, user1})
        #   9 : ({user3}, {user3, user2})
        #   11 : ({user3, user1}, {user2, user3, user1})
        #   12 : ({user3, user1}, {user2, user3, user1})
        #   13 : ({user1}, {user2, user1})
        #   14 : ({user1}, {user2, user1})
        #   16 : ({user3, user1}, {user2, user3, user1})
        #   17 : ({user3, user1}, {user2, user3, user1})
        #   19 : ({user1},{user1})
        #   20 : ({user3, user1},{user3, user1})
        #   21 : ({user3, user1},{user3, user1})
        #   22 : ({user3, user1},{user3, user1})
        #   23 : ({user3, user1},{user3, user1})
        #   24 : ({user3, user1},{user3, user1})
        #   25 : ({user3, user1},{user3, user1})
        #   26 : ({user3, user1},{user3, user1})
        # }

        self.assertNotEqual(gastos_users_dict, None)
        self.assertEqual(len(gastos_users_dict), 16)

        gastos = Gasto.objects.filter(
            usuario__in=[user1_viv, user3_viv]).order_by("id")

        ids = [g.id for g in gastos]

        expected = dict()
        expected[ids[0]] = ({user1_viv}, {user2_viv, user1_viv})
        expected[ids[1]] = ({user3_viv}, {user3_viv, user2_viv})
        expected[ids[2]] = ({user3_viv, user1_viv}, {
                            user2_viv, user3_viv, user1_viv})
        expected[ids[3]] = ({user3_viv, user1_viv}, {
                            user2_viv, user3_viv, user1_viv})
        expected[ids[4]] = ({user1_viv}, {user2_viv, user1_viv})
        expected[ids[5]] = ({user1_viv}, {user2_viv, user1_viv})
        expected[ids[6]] = ({user3_viv, user1_viv}, {
                            user2_viv, user3_viv, user1_viv})
        expected[ids[7]] = ({user3_viv, user1_viv}, {
                            user2_viv, user3_viv, user1_viv})
        expected[ids[8]] = ({user1_viv}, {user1_viv})
        expected[ids[9]] = ({user3_viv, user1_viv}, {user3_viv, user1_viv})
        expected[ids[10]] = ({user3_viv, user1_viv}, {user3_viv, user1_viv})
        expected[ids[11]] = ({user3_viv, user1_viv}, {user3_viv, user1_viv})
        expected[ids[12]] = ({user3_viv, user1_viv}, {user3_viv, user1_viv})
        expected[ids[13]] = ({user3_viv, user1_viv}, {user3_viv, user1_viv})
        expected[ids[14]] = ({user3_viv, user1_viv}, {user3_viv, user1_viv})
        expected[ids[15]] = ({user3_viv, user1_viv}, {user3_viv, user1_viv})

        for i in ids:
            self.assertEqual(
                gastos_users_dict[Gasto.objects.get(id=i)],
                expected[i],
                "assertion failed for Gasto with id=%s" % (i))

    def test_get_reversed_user_totals_dict_method_empty_gastos_dict(self):
        db = get_setup_w_vivienda_3_users_and_periods()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user1_viv = user1.get_vu()
        user2_viv = user2.get_vu()
        user3_viv = user3.get_vu()
        vivienda = db["vivienda"]

        (actual_totals,
         expected_totals) = vivienda.get_reversed_user_totals_dict({})

        self.assertEqual(actual_totals[user1_viv], 0)
        self.assertEqual(actual_totals[user2_viv], 0)
        self.assertEqual(actual_totals[user3_viv], 0)
        self.assertEqual(expected_totals[user1_viv], 0)
        self.assertEqual(expected_totals[user2_viv], 0)
        self.assertEqual(expected_totals[user3_viv], 0)

    def test_get_reversed_user_totals_dict_w_empty_gastos_dict_w_left(self):
        db = get_setup_w_vivienda_3_users_and_periods()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user1_viv = user1.get_vu()
        user3_viv = user3.get_vu()
        user2_viv = user2.get_vu()
        vivienda = db["vivienda"]

        user2_viv.fecha_abandono = db["pC"]
        user2_viv.estado = "inactivo"
        user2_viv.save()

        (actual_totals,
         expected_totals) = vivienda.get_reversed_user_totals_dict({})

        self.assertEqual(actual_totals[user1_viv], 0)
        self.assertEqual(actual_totals[user3_viv], 0)
        self.assertEqual(expected_totals[user1_viv], 0)
        self.assertEqual(expected_totals[user3_viv], 0)

        self.assertEqual(actual_totals.get(user2_viv, None), None)
        self.assertEqual(expected_totals.get(user2_viv, None), None)

    def test_get_reversed_user_totals_no_left_no_vacation(self):
        db = get_setup_w_vivienda_3_users_and_periods()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user1_viv = user1.get_vu()
        user3_viv = user3.get_vu()
        user2_viv = user2.get_vu()
        vivienda = db["vivienda"]

        all_users = {user1_viv, user2_viv, user3_viv}

        cat_shared_on_leave = db["cat_shared_on_leave"]

        gasto_1 = Gasto.objects.create(
            monto=1200,
            creado_por=user1_viv,
            categoria=cat_shared_on_leave)
        user1_viv.confirm_pay(gasto_1, fecha_pago=db["pB"])

        gasto_2 = Gasto.objects.create(
            monto=3000,
            creado_por=user2_viv,
            categoria=cat_shared_on_leave)
        user2_viv.confirm_pay(gasto_2, fecha_pago=db["pD"])

        gasto_user_dict = dict()
        gasto_user_dict[gasto_1] = (all_users, all_users)
        gasto_user_dict[gasto_2] = (all_users, all_users)

        (actual_totals,
         expected_totals) = vivienda.get_reversed_user_totals_dict(
            gasto_user_dict)

        self.assertEqual(actual_totals[user1_viv], 1200)
        self.assertEqual(actual_totals[user2_viv], 3000)
        self.assertEqual(actual_totals[user3_viv], 0)
        self.assertEqual(expected_totals[user1_viv], 1400)
        self.assertEqual(expected_totals[user2_viv], 1400)
        self.assertEqual(expected_totals[user3_viv], 1400)

    def test_get_reversed_user_totals_no_left_w_vacation(self):
        db = get_setup_w_vivienda_3_users_and_periods()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user1_viv = user1.get_vu()
        user3_viv = user3.get_vu()
        user2_viv = user2.get_vu()
        vivienda = db["vivienda"]

        vac2, __ = user2.go_on_vacation(start_date=db["pB"], end_date=db["pD"])

        vacations = [vac2]

        all_users = {user1_viv, user2_viv, user3_viv}

        cat_not_shared_on_leave = db["cat_not_shared_on_leave"]
        cat_shared_on_leave = db["cat_shared_on_leave"]

        gasto_1 = Gasto.objects.create(
            monto=1200,
            creado_por=user1_viv,
            categoria=cat_shared_on_leave)
        user1_viv.confirm_pay(gasto_1, fecha_pago=db["pB"])

        gasto_2 = Gasto.objects.create(
            monto=3000,
            creado_por=user3_viv,
            categoria=cat_not_shared_on_leave)
        user3_viv.confirm_pay(gasto_2, fecha_pago=db["pD"])

        gasto_user_dict = dict()
        gasto_user_dict[gasto_1] = (all_users, all_users)

        gasto_user_dict[gasto_2] = ({user1_viv, user3_viv},
                                    {user1_viv, user3_viv})

        (actual_totals,
         expected_totals) = vivienda.get_reversed_user_totals_dict(
            gasto_user_dict)

        self.assertEqual(actual_totals[user1_viv], 1200)
        self.assertEqual(actual_totals[user2_viv], 0)
        self.assertEqual(actual_totals[user3_viv], 3000)
        self.assertEqual(expected_totals[user1_viv], 1500 + 400)
        self.assertEqual(expected_totals[user2_viv], 400)
        self.assertEqual(expected_totals[user3_viv], 1500 + 400)

    def test_get_reversed_user_totals_w_left_w_vacation(self):
        db = get_setup_w_vivienda_3_users_and_periods()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user1_viv = user1.get_vu()
        user3_viv = user3.get_vu()
        user2_viv = user2.get_vu()
        vivienda = db["vivienda"]

        user2_viv.fecha_abandono = db["pC"]
        user2_viv.estado = "inactivo"

        user3_viv.fecha_creacion = db["pC"]

        vac1, __ = user1.go_on_vacation(start_date=db["pB"], end_date=db["pC"])
        vac3, __ = user3.go_on_vacation(start_date=db["pE"])
        vacations = {vac1, vac3}

        cat_not_shared_on_leave = db["cat_not_shared_on_leave"]
        cat_shared_on_leave = db["cat_shared_on_leave"]

        gasto_1 = Gasto.objects.create(
            monto=1200,
            creado_por=user2_viv,
            categoria=cat_not_shared_on_leave)
        user2_viv.confirm_pay(gasto_1, fecha_pago=db["pB"])

        gasto_2 = Gasto.objects.create(
            monto=1500,
            creado_por=user3_viv,
            categoria=cat_shared_on_leave)
        user3_viv.confirm_pay(gasto_2, fecha_pago=db["pC"])

        gasto_3 = Gasto.objects.create(
            monto=2000,
            creado_por=user1_viv,
            categoria=cat_shared_on_leave)
        user1_viv.confirm_pay(gasto_3, fecha_pago=db["pE"])

        # save so that the fields are actually modified
        user2_viv.save()
        user3_viv.save()

        all_users = {user1_viv, user2_viv, user3_viv}

        gasto_user_dict = dict()
        gasto_user_dict[gasto_2] = ({user1_viv, user3_viv}, all_users)
        gasto_user_dict[gasto_3] = ({user1_viv, user3_viv},
                                    {user1_viv, user3_viv})

        (actual_totals,
         expected_totals) = vivienda.get_reversed_user_totals_dict(
            gasto_user_dict)

        self.assertEqual(actual_totals.get(user2_viv, None), None)
        self.assertEqual(expected_totals.get(user2_viv, None), None)

        self.assertEqual(actual_totals[user1_viv], 2000)
        self.assertEqual(actual_totals[user3_viv], 1000)
        self.assertEqual(expected_totals[user1_viv], 1000 + 500)
        self.assertEqual(expected_totals[user3_viv], 1000 + 500)

    def test_get_reversed_user_totals_dict_hard_database(self):
        """
        Tests that the Vivienda can convert a dict of the form:
        {
            Gasto: (
                currently_active_users_that_should_pay_this_Gasto,
                users_active_at_the_time_of_Gasto_that_had_to_pay_it
            )
        }
        to 2 dicts: actual_total_per_user and expected_total_per_user.
        Both dicts are of the form:
        {User: Integer}
        The first dict represents how much the User has spent in Gastos that
        are shared with the active users, and the second dict represents how
        much the user should've spent
        """
        db = get_hard_balance_test_database()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user1_viv = db["user1_viv"]
        user2_viv = db["user2_viv"]
        user3_viv = db["user3_viv"]
        vivienda = db["vivienda"]

        active_users = {user1_viv, user3_viv}
        all_users = {user1_viv, user2_viv, user3_viv}

        vacations = vivienda.get_vacations_after_date(db["pA"])
        gastos_users_dict = vivienda.get_smart_gasto_dict(
            active_users,
            all_users,
            vacations)
        # gastos_users_dict has this values
        # (tested in test_get_smart_gasto_dict_method_hard)
        # {
        #   1 : ({user1}, {user2, user1})
        #   9 : ({user3}, {user3, user2})
        #   11 : ({user3, user1}, {user2, user3, user1})
        #   12 : ({user3, user1}, {user2, user3, user1})
        #   13 : ({user1}, {user2, user1})
        #   14 : ({user1}, {user2, user1})
        #   16 : ({user3, user1}, {user2, user3, user1})
        #   17 : ({user3, user1}, {user2, user3, user1})
        #   19 : ({user1},{user1})
        #   20 : ({user3, user1},{user3, user1})
        #   21 : ({user3, user1},{user3, user1})
        #   22 : ({user3, user1},{user3, user1})
        #   23 : ({user3, user1},{user3, user1})
        #   24 : ({user3, user1},{user3, user1})
        #   25 : ({user3, user1},{user3, user1})
        #   26 : ({user3, user1},{user3, user1})
        # }

        (actual_total_per_user,
            expected_total_per_user
         ) = vivienda.get_reversed_user_totals_dict(gastos_users_dict)

        # actual totals should look like this:
        # portions of 1000:
        # user1 : 1/2 + 1/2 + 1/2 + 2/3 + 2/3 + 1 + 5
        # user3 : 1.0/2 + 2.0/3 + 2.0/3 + 2.0
        # => user1 : 8833.333333333332
        # => user3 : 3833.333333333333

        # give some margin in assertions because of float aproximations
        self.assertAlmostEquals(sum(actual_total_per_user.values()),
                                sum(expected_total_per_user.values()))

        self.assertAlmostEqual(
            actual_total_per_user[user1_viv],
            8833,
            delta=5)
        self.assertAlmostEqual(
            actual_total_per_user[user3_viv],
            3833,
            delta=5)

        # expected_total_per_user should look like this:
        # {
        #    1: (1/2 + 2/3 + 1 + 2/3 + 1 + 7/2)*1000 = 7333.333
        #    3: (1/2 + 2/3 + 2/3 + 7/2)*1000 = 5333.333
        # }

        self.assertAlmostEqual(
            expected_total_per_user[user1_viv],
            7333,
            delta=5)
        self.assertAlmostEqual(
            expected_total_per_user[user3_viv],
            5333,
            delta=5)

    def test_get_smart_balance_no_left_no_vacation(self):
        """
        Tests that get_smart_balance correctly calls every helper method and
        returns the excepted balance dict. This is the easiest of many cases.
        """
        db = get_setup_w_vivienda_3_users_and_periods()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user1_viv = user1.get_vu()
        user3_viv = user3.get_vu()
        user2_viv = user2.get_vu()
        vivienda = db["vivienda"]

        cat_shared_on_leave = db["cat_shared_on_leave"]

        gasto_1 = Gasto.objects.create(
            monto=1200,
            creado_por=user1_viv,
            categoria=cat_shared_on_leave)
        user1_viv.confirm_pay(gasto_1, fecha_pago=db["pB"])

        gasto_2 = Gasto.objects.create(
            monto=3000,
            creado_por=user2_viv,
            categoria=cat_shared_on_leave)
        user2_viv.confirm_pay(gasto_2, fecha_pago=db["pD"])

        transfers = vivienda.get_smart_balance()

        self.assertEqual(transfers.get(user2_viv, None), None)

        self.assertEqual(
            transfers.get(user1_viv, None),
            [(user2_viv, 200)]
        )
        self.assertEqual(
            transfers.get(user3_viv, None),
            [(user2_viv, 1400)]
        )

    def test_get_smart_balance_no_left_w_vacation(self):
        db = get_setup_w_vivienda_3_users_and_periods()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user1_viv = user1.get_vu()
        user3_viv = user3.get_vu()
        user2_viv = user2.get_vu()
        vivienda = db["vivienda"]

        vac2, __ = user2.go_on_vacation(start_date=db["pB"], end_date=db["pD"])

        vacations = [vac2]

        all_users = {user1_viv, user2_viv, user3_viv}

        cat_not_shared_on_leave = db["cat_not_shared_on_leave"]
        cat_shared_on_leave = db["cat_shared_on_leave"]

        gasto_1 = Gasto.objects.create(
            monto=1200,
            creado_por=user1_viv,
            categoria=cat_shared_on_leave)
        user1_viv.confirm_pay(gasto_1, fecha_pago=db["pB"])

        gasto_2 = Gasto.objects.create(
            monto=3000,
            creado_por=user3_viv,
            categoria=cat_not_shared_on_leave)
        user3_viv.confirm_pay(gasto_2, fecha_pago=db["pD"])

        transfers = vivienda.get_smart_balance()

        self.assertEqual(
            transfers.get(user1_viv, None),
            [(user3_viv, 700)]
        )
        self.assertEqual(
            transfers.get(user2_viv, None),
            [(user3_viv, 400)]
        )
        self.assertEqual(
            transfers.get(user3_viv, None),
            None
        )

    def test_get_smart_balance_w_left_w_vacation(self):
        db = get_setup_w_vivienda_3_users_and_periods()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user1_viv = user1.get_vu()
        user3_viv = user3.get_vu()
        user2_viv = user2.get_vu()
        vivienda = db["vivienda"]

        user2_viv.fecha_abandono = db["pC"]
        user2_viv.estado = "inactivo"

        user3_viv.fecha_creacion = db["pC"]

        vac1, __ = user1.go_on_vacation(start_date=db["pB"], end_date=db["pC"])
        vac3, __ = user3.go_on_vacation(start_date=db["pE"])

        cat_not_shared_on_leave = db["cat_not_shared_on_leave"]
        cat_shared_on_leave = db["cat_shared_on_leave"]

        gasto_1 = Gasto.objects.create(
            monto=1200,
            creado_por=user2_viv,
            categoria=cat_not_shared_on_leave)
        user2_viv.confirm_pay(gasto_1, fecha_pago=db["pB"])

        gasto_2 = Gasto.objects.create(
            monto=1500,
            creado_por=user3_viv,
            categoria=cat_shared_on_leave)
        user3_viv.confirm_pay(gasto_2, fecha_pago=db["pC"])

        gasto_3 = Gasto.objects.create(
            monto=2000,
            creado_por=user1_viv,
            categoria=cat_shared_on_leave)
        user1_viv.confirm_pay(gasto_3, fecha_pago=db["pE"])

        # save so that the fields are actually modified
        user2_viv.save()
        user3_viv.save()

        transfers = vivienda.get_smart_balance()

        self.assertEqual(transfers.get(user1_viv, None), None)
        self.assertEqual(transfers.get(user2_viv, None), None)
        self.assertEqual(
            transfers.get(user3_viv, None),
            [(user1_viv, 500)]
        )

    def test_get_smart_balance_hard_database(self):
        db = get_hard_balance_test_database()

        user1_viv = db["user1_viv"]
        user2_viv = db["user2_viv"]
        user3_viv = db["user3_viv"]
        vivienda = db["vivienda"]

        transfers = vivienda.get_smart_balance()

        self.assertEqual(transfers.get(user1_viv, None), None)
        self.assertEqual(transfers.get(user2_viv, None), None)
        self.assertNotEqual(transfers.get(user3_viv, None), None)
        user_to_transfer = transfers.get(user3_viv)[0][0]
        monto_to_transfer = transfers.get(user3_viv)[0][1]
        self.assertEqual(user_to_transfer, user1_viv)
        self.assertAlmostEqual(
            monto_to_transfer,
            1500,
            delta=5
        )

    def test_get_balance_with_vacations_method_harder(self):
        db = get_setup_w_vivienda_3_users_and_periods()
        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]

        user1_viv = user1.get_vu()
        user2_viv = user2.get_vu()
        user3_viv = user3.get_vu()

        vivienda = db["vivienda"]

        user1.go_on_vacation(start_date=db["pB"], end_date=db["pD"])
        user3.go_on_vacation(start_date=db["pC"], end_date=db["pE"])

        gnsl1 = Gasto.objects.create(
            monto=1200,
            creado_por=user1.get_vu(),
            categoria=db["cat_not_shared_on_leave"])
        user1_viv.confirm_pay(gnsl1, fecha_pago=db["pA"])

        gnsl2 = Gasto.objects.create(
            monto=2000,
            creado_por=user2.get_vu(),
            categoria=db["cat_not_shared_on_leave"])
        user2_viv.confirm_pay(gnsl2, fecha_pago=db["pC"])

        gsl1 = Gasto.objects.create(
            monto=1500,
            creado_por=user3.get_vu(),
            categoria=db["cat_shared_on_leave"])
        user3_viv.confirm_pay(gsl1, fecha_pago=db["pB"])

        # periods  :    A   |    B   | C
        # gastos   :  gnsl1 |  gsl1  | gnsl2
        # users out:  none  |  user1 | (user1, user3)
        # gnsl1 should be payed by: all => +400 each
        # gsl1 should be payed by: all => +500 each
        # gnsl2 should be payed by: user2 => +2000 user2
        # users have payed: {user1:1200, user2: 2000, user3: 1500}
        # users SHOULD have payed: {user1:900, user2: 2900, user3: 900}

        transfers = vivienda.get_smart_balance()

        # result dict should be:
        # {user2_viv: [(user1_viv, 300), (user3_viv, 600)]}
        self.assertEqual(transfers.get(user1_viv, None), None)
        self.assertEqual(transfers.get(user3_viv, None), None)

        user2_transfers = transfers.get(user2_viv, None)
        self.assertNotEqual(user2_transfers, None)
        self.assertEqual(len(user2_transfers), 2)
        self.assertEqual(
            set(user2_transfers),
            {(user1_viv, 300), (user3_viv, 600)}
        )

    def test_get_smart_gasto_dict_hardest(self):
        db = get_HARDEST_balance_test_database()

        user1_viv = db["user1_viv"]
        user2_viv = db["user2_viv"]
        user3_viv = db["user3_viv"]
        user4_viv = db["user4_viv"]
        user5_viv = db["user5_viv"]
        vivienda = db["vivienda"]

        active_users = {user1_viv, user4_viv, user5_viv}
        all_users = {user1_viv, user2_viv, user3_viv, user4_viv, user5_viv}

        vacations = vivienda.get_vacations_after_date(db["pA"])

        gastos_users_dict = vivienda.get_smart_gasto_dict(
            active_users,
            all_users,
            vacations)

        ids = [g.id for g in gastos_users_dict]
        ids.sort()

        expected = dict()

        # the resulting dict should look like this:
        # (this was computed by hand)
        expected[ids[0]] = ({user1_viv}, {user1_viv, user2_viv})
        expected[ids[1]] = ({user1_viv}, {user1_viv, user2_viv})
        expected[ids[2]] = ({user1_viv, user4_viv}, {user1_viv, user4_viv})
        expected[ids[3]] = ({user1_viv, user4_viv}, {user1_viv, user4_viv})
        expected[ids[4]] = (
            {user1_viv, user4_viv}, {user1_viv, user2_viv, user4_viv})
        expected[ids[5]] = (
            {user1_viv, user4_viv}, {user1_viv, user3_viv, user4_viv})
        expected[ids[6]] = (
            {user1_viv, user4_viv}, {user1_viv, user2_viv, user3_viv,
                                     user4_viv})
        expected[ids[7]] = (
            {user1_viv, user4_viv}, {user1_viv, user3_viv, user4_viv})
        expected[ids[8]] = (
            {user1_viv, user4_viv}, {user1_viv, user3_viv, user4_viv})
        expected[ids[9]] = (
            {user1_viv, user4_viv}, {user1_viv, user2_viv, user3_viv,
                                     user4_viv})
        expected[ids[10]] = (
            {user1_viv, user4_viv}, {user1_viv, user2_viv, user3_viv,
                                     user4_viv})
        expected[ids[11]] = ({user4_viv}, {user4_viv})
        expected[ids[12]] = ({user4_viv}, {user4_viv})
        expected[ids[13]] = ({user4_viv}, {user4_viv})
        expected[ids[14]] = (
            {user1_viv, user4_viv}, {user1_viv, user3_viv, user4_viv})
        expected[ids[15]] = ({user1_viv}, {user1_viv, user3_viv})
        expected[ids[16]] = (
            {user1_viv, user4_viv}, {user1_viv, user3_viv, user4_viv})
        expected[ids[17]] = (
            {user1_viv, user4_viv}, {user1_viv, user3_viv, user4_viv})
        expected[ids[18]] = (
            {user1_viv, user4_viv}, {user1_viv, user3_viv, user4_viv})
        expected[ids[19]] = (
            {user1_viv, user4_viv}, {user1_viv, user3_viv, user4_viv})
        expected[ids[20]] = (
            {user1_viv, user4_viv}, {user1_viv, user3_viv, user4_viv})
        expected[ids[21]] = ({user4_viv, user5_viv}, {user4_viv, user5_viv})
        expected[ids[22]] = (
            {user1_viv, user4_viv, user5_viv}, {user1_viv, user4_viv,
                                                user5_viv})
        expected[ids[23]] = (
            {user1_viv, user4_viv, user5_viv}, {user1_viv, user4_viv,
                                                user5_viv})
        expected[ids[24]] = (
            {user1_viv, user4_viv, user5_viv}, {user1_viv, user4_viv,
                                                user5_viv})
        expected[ids[25]] = ({user5_viv}, {user5_viv})
        expected[ids[26]] = ({user5_viv}, {user5_viv})
        expected[ids[27]] = ({user5_viv}, {user5_viv})
        expected[ids[28]] = (
            {user1_viv, user4_viv, user5_viv}, {user1_viv, user4_viv,
                                                user5_viv})
        expected[ids[29]] = ({user5_viv}, {user5_viv})
        expected[ids[30]] = (
            {user1_viv, user4_viv, user5_viv}, {user1_viv, user4_viv,
                                                user5_viv})
        expected[ids[31]] = (
            {user1_viv, user4_viv, user5_viv}, {user1_viv, user4_viv,
                                                user5_viv})
        expected[ids[32]] = (
            {user1_viv, user4_viv, user5_viv}, {user1_viv, user4_viv,
                                                user5_viv})
        expected[ids[33]] = (
            {user1_viv, user4_viv, user5_viv}, {user1_viv, user4_viv,
                                                user5_viv})
        expected[ids[34]] = (
            {user1_viv, user4_viv, user5_viv}, {user1_viv, user4_viv,
                                                user5_viv})
        expected[ids[35]] = (
            {user1_viv, user4_viv, user5_viv}, {user1_viv, user4_viv,
                                                user5_viv})
        expected[ids[36]] = (
            {user1_viv, user4_viv, user5_viv}, {user1_viv, user4_viv,
                                                user5_viv})
        expected[ids[37]] = (
            {user1_viv, user4_viv, user5_viv}, {user1_viv, user4_viv,
                                                user5_viv})
        expected[ids[38]] = (
            {user1_viv, user4_viv, user5_viv}, {user1_viv, user4_viv,
                                                user5_viv})

        for id in ids:
            gasto = Gasto.objects.get(id=id)
            self.assertNotEqual(
                gastos_users_dict.get(gasto, None),
                None,
                "Gasto with id=%d is not in resulting smart dict" % (id)
            )
            self.assertEqual(
                gastos_users_dict.get(gasto, None),
                expected.get(id, None),
                "Gasto with id=%d is not equal to expected" % (id)
            )

    def test_get_reversed_user_totals_hardest(self):
        db = get_HARDEST_balance_test_database()

        user1_viv = db["user1_viv"]
        user2_viv = db["user2_viv"]
        user3_viv = db["user3_viv"]
        user4_viv = db["user4_viv"]
        user5_viv = db["user5_viv"]
        vivienda = db["vivienda"]

        active_users = {user1_viv, user4_viv, user5_viv}
        all_users = {user1_viv, user2_viv, user3_viv, user4_viv, user5_viv}

        vacations = vivienda.get_vacations_after_date(db["pA"])

        gastos_users_dict = vivienda.get_smart_gasto_dict(
            active_users,
            all_users,
            vacations)  # this method is already tested

        (actual_totals,
         expected_totals
         ) = vivienda.get_reversed_user_totals_dict(gastos_users_dict)

        self.assertAlmostEqual(
            sum(actual_totals.values()),
            sum(expected_totals.values()),
            delta=5
        )
        self.assertEqual(actual_totals.get(user2_viv, None), None)
        self.assertEqual(actual_totals.get(user3_viv, None), None)
        self.assertEqual(expected_totals.get(user2_viv, None), None)
        self.assertEqual(expected_totals.get(user3_viv, None), None)

        # actual totals should look like this:
        # user1_viv: 9666.666666666666
        # user4_viv: 11000.0
        # user5_viv: 12000.0

        self.assertAlmostEqual(
            actual_totals.get(user1_viv, None),
            9666.666666666666,
            delta=5
        )
        self.assertAlmostEqual(
            actual_totals.get(user4_viv, None),
            11000.0,
            delta=5
        )
        self.assertAlmostEqual(
            actual_totals.get(user5_viv, None),
            12000.0,
            delta=5
        )

        # the expected totals should be:
        # (calculated by hand)
        # user1_viv: 10916.666666666668
        # user4_viv: 12916.666666666668
        # user5_viv: 8833.333333333332

        self.assertAlmostEqual(
            expected_totals.get(user1_viv, None),
            10916.666666666668,
            delta=5
        )
        self.assertAlmostEqual(
            expected_totals.get(user4_viv, None),
            12916.666666666668,
            delta=5
        )
        self.assertAlmostEqual(
            expected_totals.get(user5_viv, None),
            8833.333333333332,
            delta=5
        )

    def test_get_smart_balance_hardest(self):
        db = get_HARDEST_balance_test_database()

        user1_viv = db["user1_viv"]
        user2_viv = db["user2_viv"]
        user3_viv = db["user3_viv"]
        user4_viv = db["user4_viv"]
        user5_viv = db["user5_viv"]
        vivienda = db["vivienda"]

        transfers = vivienda.get_smart_balance()

        # users that are not currently active shoudn't show up in the balance
        self.assertEqual(transfers.get(user2_viv, None), None)
        self.assertEqual(transfers.get(user3_viv, None), None)

        # actual totals should look like this:
        # user1_viv: 9666.666666666666
        # user4_viv: 11000.0
        # user5_viv: 12000.0

        # the expected totals should be:
        # (calculated by hand)
        # user1_viv: 10916.666666666668
        # user4_viv: 12916.666666666668
        # user5_viv: 8833.333333333332

        # Therefore, the balance should look like this:
        # 1: -1250
        # 4: −1916.666
        # 5: 3166,667
        # and the insructions would look like this:

        user1_transfer = transfers.get(user1_viv, None)
        self.assertNotEqual(user1_transfer, None)
        self.assertEqual(user1_transfer[0][0], user5_viv)
        self.assertAlmostEqual(
            user1_transfer[0][1],
            1250,
            delta=5
        )

        user4_transfer = transfers.get(user4_viv, None)
        self.assertNotEqual(user4_transfer, None)
        self.assertEqual(user4_transfer[0][0], user5_viv)
        self.assertAlmostEqual(
            user4_transfer[0][1],
            1916.666,
            delta=5
        )


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
        user1_viv.confirm_pay(gasto)

        gastos_pendientes, gastos_pagados = user1_viv.get_gastos_vivienda()

        self.assertEqual(gastos_pendientes.count(), 0)
        self.assertEqual(gastos_pagados.count(), 1)

    def test_user_gets_gastos_of_viv_that_has_gastos_pend_and_pays_them(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        gasto, dummy_categoria = get_dummy_gasto_pendiente(user1_viv)
        user1_viv.confirm_pay(gasto)

        gastos_pendientes, gastos_pagados = user1_viv.get_gastos_vivienda()

        self.assertEqual(gastos_pendientes.count(), 0)
        self.assertEqual(gastos_pagados.count(), 1)

    def test_user_invites_another(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        user2 = ProxyUser.objects.create(username="us2", email="b@b.com")
        invite = Invitacion.objects.create(
            invitado=user2, invitado_por=user1_viv, email="b@b.com")

        self.assertTrue(user1_viv.sent_invite(invite))


class UserIsOutModelTest(TestCase):

    def test_pass(self):
        pass


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
        gasto_2.confirm_pay(user1_viv)

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
        gasto_1.confirm_pay(user1_viv)
        gasto_2.confirm_pay(user1_viv)

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

    def test_pay_method_1_user(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        gasto, dummy_categoria = get_dummy_gasto_pendiente(user1_viv)

        gasto.pay(user1_viv)

        self.assertTrue(gasto.is_paid())
        self.assertFalse(gasto.is_pending())
        self.assertFalse(gasto.is_pending_confirm())

    def test_pay_method_many_users(self):
        (user1,
         user2,
         correct_vivienda,
         user1_viv, user2_viv) = get_vivienda_with_2_users()
        gasto, dummy_categoria = get_dummy_gasto_pendiente(user1_viv)

        gasto.pay(user1_viv)

        self.assertFalse(gasto.is_paid())
        self.assertFalse(gasto.is_pending())
        self.assertTrue(gasto.is_pending_confirm())

    def test_confirm_pay_method(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        gasto, dummy_categoria = get_dummy_gasto_pendiente(user1_viv)

        gasto.confirm_pay(user1_viv)

        self.assertTrue(gasto.is_paid())
        self.assertFalse(gasto.is_pending())
        self.assertEqual(gasto.estado.estado, "pagado")

    def test_allow_user(self):
        user1, correct_vivienda, user1_viv = get_vivienda_with_1_user()
        user2 = ProxyUser.objects.create(username="us2", email="b@b.com")
        gasto, dummy_categoria = get_dummy_gasto_pendiente(user1_viv)

        self.assertTrue(gasto.allow_user(user1))
        self.assertFalse(gasto.allow_user(user2))
