from django.test import TestCase
from django.utils import timezone
from expenses_manager.models import *
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
        user1.pagar(gasto)
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
        p1 = YearMonth.objects.create(year=2016, month=1)
        p2 = YearMonth.objects.create(year=2016, month=2)
        # create 2 gastos per user, using different combinations
        # of A,B and P1, P2
        estado_pagado = EstadoGasto.objects.create(estado="pagado")
        # gastos user1
        g1_1 = Gasto.objects.create(
            monto=1000,
            creado_por=user1.get_vu(),
            usuario=user1.get_vu(),
            categoria=cat_1,
            year_month=p1,
            estado=estado_pagado)
        g1_2 = Gasto.objects.create(
            monto=2000,
            creado_por=user1.get_vu(),
            usuario=user1.get_vu(),
            categoria=cat_2,
            year_month=p1,
            estado=estado_pagado)
        # gastos user2
        g2_1 = Gasto.objects.create(
            monto=500,
            creado_por=user2.get_vu(),
            usuario=user2.get_vu(),
            categoria=cat_1,
            year_month=p1,
            estado=estado_pagado)
        g2_2 = Gasto.objects.create(
            monto=1700,
            creado_por=user2.get_vu(),
            usuario=user2.get_vu(),
            categoria=cat_2,
            year_month=p2,
            estado=estado_pagado)
        # gastos user3
        g3_1 = Gasto.objects.create(
            monto=1200,
            creado_por=user3.get_vu(),
            usuario=user3.get_vu(),
            categoria=cat_1,
            year_month=p1,
            estado=estado_pagado)
        g3_2 = Gasto.objects.create(
            monto=700,
            creado_por=user3.get_vu(),
            usuario=user3.get_vu(),
            categoria=cat_1,
            year_month=p1,
            estado=estado_pagado)

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
        total_per_user = vivienda.get_total_expenses_per_active_user()
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
        self.assertEqual(total_per_user[user1], 3000)
        # user2 should have 2200 total
        self.assertEqual(total_per_user[user2], 2200)
        # user3 should have 1900 total
        self.assertEqual(total_per_user[user3], 1900)

        # TRANSFER METHOD CALL!!
        # user1 has spent way too much money! He can't even buy lunch anymore!
        # let's have user2 transfer him some money to balance things up a bit
        transfer_pos, transfer_neg = user2.transfer(user1, 400)

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
        new_total_per_user = vivienda.get_total_expenses_per_active_user()
        # user1 should now have 2600 total
        self.assertNotEqual(total_per_user[user1], new_total_per_user[user1])
        self.assertEqual(new_total_per_user[user1], 2600)
        # user2 should now have 2600 total
        self.assertNotEqual(total_per_user[user2], new_total_per_user[user2])
        self.assertEqual(new_total_per_user[user2], 2600)
        # user3 should still have 1900 total
        self.assertEqual(total_per_user[user3], new_total_per_user[user3])
        self.assertEqual(new_total_per_user[user3], 1900)

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
        user1.pagar(gasto)

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
        vivienda = db["vivienda"]
        user1.go_on_vacation(start_date=db["pB"], end_date=db["pD"])
        # user3 is out from period C-E
        user3.go_on_vacation(start_date=db["pC"], end_date=db["pE"])
        # Gnsl1 = user1 makes gasto cat_not_shared_on_leave on A for 1200
        Gnsl1 = Gasto.objects.create(
            monto=1200,
            creado_por=user1.get_vu(),
            categoria=db["cat_not_shared_on_leave"])
        user1.pagar(Gnsl1, fecha_pago=db["pA"])
        # Gnsl2 = user2 makes gasto cat_not_shared_on_leave on C for 2000
        Gnsl2 = Gasto.objects.create(
            monto=2000,
            creado_por=user2.get_vu(),
            categoria=db["cat_not_shared_on_leave"])
        user2.pagar(Gnsl2, fecha_pago=db["pC"])
        # Gsl1 = user3 makes gasto cat_shared_on_leave on B for 1500
        Gsl1 = Gasto.objects.create(
            monto=1500,
            creado_por=user3.get_vu(),
            categoria=db["cat_shared_on_leave"])
        user3.pagar(Gsl1, fecha_pago=db["pB"])
        # periods  :    A   |    B   | C
        # gastos   :  Gnsl1 |  Gsl1  | Gnsl2
        # users out:  none  |  user1 | (user1, user3)
        # Gnsl1 should be payed by: all => +400 each
        # Gsl1 should be payed by: all => +500 each
        # Gnsl2 should be payed by: user2 => +2000 user2
        # users have payed: {user1:1200, user2: 2000, user3: 1500}

        total_per_user = vivienda.get_expected_total_per_active_user_with_vacations()

        # users SHOULD have payed: {user1:900, user2: 2900, user3: 900}
        self.assertEqual(total_per_user.get(user1, None), 900)
        self.assertEqual(total_per_user.get(user2, None), 2900)
        self.assertEqual(total_per_user.get(user3, None), 900)

    def test_compute_balance_method(self):
        db = get_setup_w_vivienda_3_users_and_periods()
        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        vivienda = db["vivienda"]

        actual_total = {user1: 1200, user2: 2000, user3: 1500}
        expected_total = {user1: 900, user2: 2900, user3: 900}

        balance = vivienda.compute_balance(actual_total, expected_total)

        # result dict should be:
        # {user2: [(user1, 300), (user3, 600)]}
        self.assertEqual(balance.get(user1, None), None)
        self.assertEqual(balance.get(user3, None), None)

        user2_transfers = balance.get(user2, None)
        self.assertNotEqual(user2_transfers, None)
        self.assertEqual(len(user2_transfers), 2)
        self.assertEqual(
            set(user2_transfers),
            set([(user1, 300), (user3, 600)])
        )

    def test_compute_balance_method_already_balanced(self):
        db = get_setup_w_vivienda_3_users_and_periods()
        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        vivienda = db["vivienda"]

        actual_total = {user1: 1200, user2: 2000, user3: 1500}
        expected_total = {user1: 1200, user2: 2000, user3: 1500}

        balance = vivienda.compute_balance(actual_total, expected_total)

        # result dict should be empty
        self.assertEqual(balance.get(user1, None), None)
        self.assertEqual(balance.get(user2, None), None)
        self.assertEqual(balance.get(user3, None), None)
        self.assertEqual(len(balance), 0)

    def test_compute_balance_method_hard(self):
        db = get_setup_w_vivienda_3_users_and_periods()
        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        vivienda = db["vivienda"]
        user4 = ProxyUser.objects.create(username="us4", email="d@d.com")
        user4_viv = ViviendaUsuario.objects.create(
            vivienda=vivienda, user=user4)

        actual_total = {
            user1: 2000,
            user2: 5000,
            user3: 1500,
            user4: 9000}
        expected_total = {
            user1: 3000,
            user2: 2500,
            user3: 7000,
            user4: 5000}

        balance = vivienda.compute_balance(actual_total, expected_total)

        self.assertEqual(balance.get(user2, None), None)
        self.assertEqual(balance.get(user4, None), None)

        user1_transfers = balance.get(user1, None)
        self.assertNotEqual(user1_transfers, None)
        self.assertEqual(len(user1_transfers), 1)
        self.assertEqual(
            set(user1_transfers),
            set([(user2, 1000)])
        )
        user3_transfers = balance.get(user3, None)
        self.assertNotEqual(user3_transfers, None)
        self.assertEqual(len(user3_transfers), 2)
        self.assertEqual(
            set(user3_transfers),
            set([(user2, 1500), (user4, 4000)])
        )

    def test_get_balance_with_vacations_method(self):
        db = get_setup_w_vivienda_3_users_and_periods()
        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        vivienda = db["vivienda"]

        # periods A,B,C,D,E
        pA = db["pA"]
        pB = db["pB"]
        pC = db["pC"]
        pD = db["pD"]
        pE = db["pE"]
        # user1 is out from period B-D
        user1.go_on_vacation(start_date=pB, end_date=pD)
        # user3 is out from period C-E
        user3.go_on_vacation(start_date=pC, end_date=pE)
        # Gnsl1 = user1 makes gasto cat_not_shared_on_leave on A for 1200
        Gnsl1 = Gasto.objects.create(
            monto=1200,
            creado_por=user1.get_vu(),
            categoria=db["cat_not_shared_on_leave"])
        user1.pagar(Gnsl1, fecha_pago=pA)
        # Gnsl2 = user2 makes gasto cat_not_shared_on_leave on C for 2000
        Gnsl2 = Gasto.objects.create(
            monto=2000,
            creado_por=user2.get_vu(),
            categoria=db["cat_not_shared_on_leave"])
        user2.pagar(Gnsl2, fecha_pago=pC)
        # Gsl1 = user3 makes gasto cat_shared_on_leave on B for 1500
        Gsl1 = Gasto.objects.create(
            monto=1500,
            creado_por=user3.get_vu(),
            categoria=db["cat_shared_on_leave"])
        user3.pagar(Gsl1, fecha_pago=pB)
        # periods  :    A   |    B   | C
        # gastos   :  Gnsl1 |  Gsl1  | Gnsl2
        # users out:  none  |  user1 | (user1, user3)
        # Gnsl1 should be payed by: all => +400 each
        # Gsl1 should be payed by: all => +500 each
        # Gnsl2 should be payed by: user2 => +2000 user2
        # users have payed: {user1:1200, user2: 2000, user3: 1500}
        # users SHOULD have payed: {user1:900, user2: 2900, user3: 900}

        balance = vivienda.get_balance_with_vacations()

        # result dict should be:
        # {user2: [(user1, 300), (user3, 600)]}
        self.assertEqual(balance.get(user1, None), None)
        self.assertEqual(balance.get(user3, None), None)

        user2_transfers = balance.get(user2, None)
        self.assertNotEqual(user2_transfers, None)
        self.assertEqual(len(user2_transfers), 2)
        self.assertEqual(
            set(user2_transfers),
            set([(user1, 300), (user3, 600)])
        )

    def test_get_total_expenses_per_active_user_method_complex_DB(self):
        db = get_HARDEST_balance_test_database()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user4 = db["user4"]
        user5 = db["user5"]
        vivienda = db["vivienda"]

        # NAIVE totals per user
        # 1: N:9000 S:5000 -> 14000
        # 2: N:4000 S:3000 -> 7000
        # 3: N:2000 S:6000 -> 8000
        # 4: N:7000 S:6000 -> 13000
        # 5: N:5000 S:7000 -> 12000
        # total:
        # 9000 + 5000 + 4000 + 3000 + 2000 + 6000 + 7000 + 6000 + 5000 + 7000
        # = 54000

        # IMPORTANT Explanation:
        # this is NAIVE because there was a time when user1 was spending
        # money for himself and user2, but user5 was not a part of
        # the Vivienda. user2 is no longer a part of the Vivienda, meaning
        # that user5 should not PERCEIVE that user1 spent that money.

        # If he did perceive this, it would unbalance the amounts spent
        # by each user (1 and 5), thus creating an error:
        # user5 is not responsable for balancing THOSE Gastos,
        # because he was not even there.

        total_per_user = vivienda.get_total_expenses_per_active_user()

        self.assertEqual(total_per_user[user1], 14000)
        self.assertEqual(total_per_user.get(user2, None), None)
        self.assertEqual(total_per_user.get(user3, None), None)
        self.assertEqual(total_per_user[user4], 13000)
        self.assertEqual(total_per_user[user5], 12000)

    def test_total_per_user_active_share_only_complex_DB(self):
        db = get_HARDEST_balance_test_database()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user4 = db["user4"]
        user5 = db["user5"]
        vivienda = db["vivienda"]


        tot_p_user_active_share = vivienda.total_per_user_active_share_only()
        # adding everything "by hand"
        # yields this:
        # {
        #     1: 8166.666666666666,
        #     4: 7333.333333333332,
        #     5: 6833.333333333331
        # }


        # IMPORTANT Explanation:
        # Q: why is this LESS than the NAIVE method?

        # A: Supose there was a time when users 1 and 2 were sharing expenses,
        # but user 5 was not a part of the Vivienda yet. Furthermore, user2
        # is no longer a part of the vivienda. Thus, if user1 spent money when
        # only 1 and 2 were roommates, user5 should not PERCEIVE this Gasto.
        # If user1 was awarded that whole Gasto's monto, then
        # this would unbalance the total amounts per user, because this would
        # mean user5 is ALSO responsable for a portion of that Gasto.

        # user5 should perceive that user1 spent that money at the time,
        # but only half of it was for himself (because it was shared with
        # user2). user1 should be awarded part of that expense: the portion
        # of it that was shared with users that are still active TODAY.

        # For instance, suppose there was a time when users 1,2 and 4 shared
        # the Vivienda, and user1 made a Gasto for 1000. However, today only
        # 1,4 and 5 share the Vivienda. This would mean that 2/3 of that
        # Gasto's monto should be added to the total of user1.
        # Why?
        # Because user1 and user4 (2 users) perceived that gasto, but it was
        # also split with user2 at the time (3 users), meaning it was split
        # into 3 parts. However, only 2 of those 3 users are still active
        # => only 2/3 parts of the monto should be added to user1.
        # The ther 1/3 part is assumed to have been balanced with user2 before
        # she/he left.

        self.assertEqual(int(tot_p_user_active_share[user1]), 8166)
        self.assertEqual(tot_p_user_active_share.get(user2, None), None)
        self.assertEqual(tot_p_user_active_share.get(user3, None), None)
        self.assertEqual(int(tot_p_user_active_share[user4]), 7333)
        self.assertEqual(int(tot_p_user_active_share[user5]), 6833)

    def test_get_balance_with_vacations_method_complex_DB(self):
        db = get_HARDEST_balance_test_database()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user4 = db["user4"]
        user5 = db["user5"]
        vivienda = db["vivienda"]

        expected = vivienda.get_expected_total_per_active_user_with_vacations()

        # adding everything "by hand"
        # yields this:
        # {
        #     1: 15333.333333333345,
        #     2: 4333.333333333333,
        #     3: 8166.666666666664,
        #     4: 17333.333333333343,
        #     5: 8833.333333333332
        # }
        # sum is 54000.000000000015 (close enough)

        self.assertEqual(int(expected[user1]), 15333)
        self.assertEqual(expected.get(user2, None), None)
        self.assertEqual(expected.get(user3, None), None)
        self.assertEqual(int(expected[user4]), 17333)
        self.assertEqual(int(expected[user5]), 8833)

        balance = vivienda.get_balance_with_vacations()

        self.assertNotEqual(balance, None)
        self.fail()

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
