# -*- coding: utf-8 -*-
from django.test import TestCase

from expenses_manager.test_utils import *
from expenses_manager.utils import rm_not_active_at_date, rm_users_out_at_date, \
	compute_balance


class StaticBalanceFunctionsTest(TestCase):

    def test_rm_users_out_at_date_method(self):
        db = get_setup_w_vivienda_3_users_and_periods()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user1_viv = user1.get_vu()
        user3_viv = user3.get_vu()
        vivienda = db["vivienda"]

        vac1, __ = user1.go_on_vacation(start_date=db["pA"], end_date=db["pC"])
        vac2, __ = user2.go_on_vacation(start_date=db["pA"], end_date=db["pB"])
        vac3, __ = user3.go_on_vacation(start_date=db["pC"], end_date=db["pE"])

        user2_viv = user2.get_vu()
        user2_viv.fecha_creacion = db["pA"]
        user2_viv.fecha_abandono = db["pC"]
        user2_viv.estado = "inactivo"
        user2_viv.save()

        vacations = {
            user1_viv: [vac1],
            user2_viv: [vac2],
            user3_viv: [vac3]
        }
        in_at_a = rm_users_out_at_date(
            {
                user1_viv,
                user2_viv,
                user3_viv
            },
            vacations,
            db["pA"])
        in_at_b = rm_users_out_at_date(
            {user1_viv, user2_viv, user3_viv},
            vacations,
            db["pB"])
        in_at_c = rm_users_out_at_date(
            {user1_viv, user2_viv, user3_viv},
            vacations,
            db["pC"])
        in_at_d = rm_users_out_at_date(
            {user1_viv, user3_viv},
            vacations,
            db["pD"])
        in_at_e = rm_users_out_at_date(
            {user1_viv, user3_viv},
            vacations,
            db["pE"])
        in_at_f = rm_users_out_at_date(
            {user1_viv, user3_viv},
            vacations,
            db["pF"])

        # for each period, check which users should be out and which
        # ones should not
        self.assertEqual(in_at_a, {user3_viv})
        self.assertEqual(in_at_b, {user3_viv})
        self.assertEqual(in_at_c, {user2_viv})
        self.assertEqual(in_at_d, {user1_viv})
        self.assertEqual(in_at_e, {user1_viv})
        self.assertEqual(in_at_f, {user1_viv, user3_viv})

    def test_rm_users_out_at_date_method_no_vacations(self):
        db = get_setup_w_vivienda_3_users_and_periods()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user1_viv = user1.get_vu()
        user3_viv = user3.get_vu()
        vivienda = db["vivienda"]

        user2_viv = user2.get_vu()
        user2_viv.fecha_creacion = db["pA"]
        user2_viv.fecha_abandono = db["pC"]
        user2_viv.estado = "inactivo"
        user2_viv.save()

        vacations = dict()

        in_at_a = rm_users_out_at_date(
            {user1_viv, user2_viv, user3_viv},
            vacations,
            db["pA"])
        in_at_b = rm_users_out_at_date(
            {user1_viv, user2_viv, user3_viv},
            vacations,
            db["pB"])
        in_at_c = rm_users_out_at_date(
            {user1_viv, user2_viv, user3_viv},
            vacations,
            db["pC"])
        in_at_d = rm_users_out_at_date(
            {user1_viv, user3_viv},
            vacations,
            db["pD"])
        in_at_e = rm_users_out_at_date(
            {user1_viv, user3_viv},
            vacations,
            db["pE"])
        in_at_f = rm_users_out_at_date(
            {user1_viv, user3_viv},
            vacations,
            db["pF"])

        # for each period, check which users should be out and which
        # ones should not
        self.assertEqual(in_at_a, {user1_viv, user2_viv, user3_viv})
        self.assertEqual(in_at_b, {user1_viv, user2_viv, user3_viv})
        self.assertEqual(in_at_c, {user1_viv, user2_viv, user3_viv})
        self.assertEqual(in_at_d, {user1_viv, user3_viv})
        self.assertEqual(in_at_e, {user1_viv, user3_viv})
        self.assertEqual(in_at_f, {user1_viv, user3_viv})

    def test_rm_users_out_at_date_method_infinite_vacation(self):
        db = get_setup_w_vivienda_3_users_and_periods()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user1_viv = user1.get_vu()
        user3_viv = user3.get_vu()
        vivienda = db["vivienda"]

        vac1, __ = user1.go_on_vacation(start_date=db["pB"])
        vac2, __ = user2.go_on_vacation(start_date=db["pA"], end_date=db["pB"])
        vac3, __ = user3.go_on_vacation(start_date=db["pC"], end_date=db["pD"])

        user2_viv = user2.get_vu()
        user2_viv.fecha_creacion = db["pA"]
        user2_viv.fecha_abandono = db["pD"]
        user2_viv.estado = "inactivo"
        user2_viv.save()

        vacations = {
            user1_viv: [vac1],
            user2_viv: [vac2],
            user3_viv: [vac3]
        }
        in_at_a = rm_users_out_at_date(
            {user1_viv, user2_viv, user3_viv},
            vacations,
            db["pA"])
        in_at_b = rm_users_out_at_date(
            {user1_viv, user2_viv, user3_viv},
            vacations,
            db["pB"])
        in_at_c = rm_users_out_at_date(
            {user1_viv, user2_viv, user3_viv},
            vacations,
            db["pC"])
        in_at_d = rm_users_out_at_date(
            {user1_viv, user2_viv, user3_viv},
            vacations,
            db["pD"])
        in_at_e = rm_users_out_at_date(
            {user1_viv, user3_viv},
            vacations,
            db["pE"])
        in_at_f = rm_users_out_at_date(
            {user1_viv, user3_viv},
            vacations,
            db["pF"])

        # for each period, check which users should be out and which
        # ones should not
        self.assertEqual(in_at_a, {user1_viv, user3_viv})
        self.assertEqual(in_at_b, {user3_viv})
        self.assertEqual(in_at_c, {user2_viv})
        self.assertEqual(in_at_d, {user2_viv})
        self.assertEqual(in_at_e, {user3_viv})
        self.assertEqual(in_at_f, {user3_viv})

    def test_rm_users_out_at_date_method_multiple_vacations_per_user(self):
        db = get_setup_w_vivienda_3_users_and_periods()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user1_viv = user1.get_vu()
        user3_viv = user3.get_vu()
        vivienda = db["vivienda"]

        vac1, __ = user1.go_on_vacation(start_date=db["pA"], end_date=db["pB"])
        vac2, __ = user1.go_on_vacation(start_date=db["pE"], end_date=db["pF"])
        vac3, __ = user2.go_on_vacation(start_date=db["pB"], end_date=db["pC"])

        user2_viv = user2.get_vu()
        user2_viv.fecha_creacion = db["pA"]
        user2_viv.fecha_abandono = db["pD"]
        user2_viv.estado = "inactivo"
        user2_viv.save()

        vacations = {
            user1_viv: [vac1, vac2],
            user2_viv: [vac3]
        }
        in_at_a = rm_users_out_at_date(
            {user1_viv, user2_viv, user3_viv},
            vacations,
            db["pA"])
        in_at_b = rm_users_out_at_date(
            {user1_viv, user2_viv, user3_viv},
            vacations,
            db["pB"])
        in_at_c = rm_users_out_at_date(
            {user1_viv, user2_viv, user3_viv},
            vacations,
            db["pC"])
        in_at_d = rm_users_out_at_date(
            {user1_viv, user2_viv, user3_viv},
            vacations,
            db["pD"])
        in_at_e = rm_users_out_at_date(
            {user1_viv, user3_viv},
            vacations,
            db["pE"])
        in_at_f = rm_users_out_at_date(
            {user1_viv, user3_viv},
            vacations,
            db["pF"])

        # for each period, check which users should be out and which
        # ones should not
        self.assertEqual(in_at_a, {user2_viv, user3_viv})
        self.assertEqual(in_at_b, {user3_viv})
        self.assertEqual(in_at_c, {user1_viv, user3_viv})
        self.assertEqual(in_at_d, {user1_viv, user2_viv, user3_viv})
        self.assertEqual(in_at_e, {user3_viv})
        self.assertEqual(in_at_f, {user3_viv})

    def test_rm_not_active_at_date_method(self):
        db = get_setup_w_vivienda_3_users_and_periods()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user1_viv = user1.get_vu()
        user3_viv = user3.get_vu()
        vivienda = db["vivienda"]

        user2_viv = user2.get_vu()
        user2_viv.fecha_creacion = db["pA"]
        user2_viv.fecha_abandono = db["pD"]
        user2_viv.estado = "inactivo"
        user2_viv.save()

        all_users = {user1_viv, user2_viv, user3_viv}

        active_at_a = rm_not_active_at_date(all_users, db["pA"])
        active_at_b = rm_not_active_at_date(all_users, db["pB"])
        active_at_c = rm_not_active_at_date(all_users, db["pC"])
        active_at_d = rm_not_active_at_date(all_users, db["pD"])
        active_at_e = rm_not_active_at_date(all_users, db["pE"])
        active_at_f = rm_not_active_at_date(all_users, db["pF"])

        self.assertEqual(active_at_a, {user1_viv, user2_viv, user3_viv})
        self.assertEqual(active_at_b, {user1_viv, user2_viv, user3_viv})
        self.assertEqual(active_at_c, {user1_viv, user2_viv, user3_viv})
        self.assertEqual(active_at_d, {user1_viv, user2_viv, user3_viv})
        self.assertEqual(active_at_e, {user1_viv, user3_viv})
        self.assertEqual(active_at_f, {user1_viv, user3_viv})

    def test_rm_not_active_at_date_method_only_one_left(self):
        db = get_setup_w_vivienda_3_users_and_periods()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user1_viv = user1.get_vu()
        user3_viv = user3.get_vu()
        user2_viv = user2.get_vu()
        vivienda = db["vivienda"]

        user1_viv.fecha_creacion = db["pA"]
        user1_viv.fecha_abandono = db["pC"]
        user1_viv.estado = "inactivo"
        user1_viv.save()

        user2_viv.fecha_creacion = db["pC"]
        user2_viv.save()

        user3_viv.fecha_creacion = db["pB"]
        user3_viv.fecha_abandono = db["pD"]
        user3_viv.estado = "inactivo"
        user3_viv.save()

        all_users = {user1_viv, user2_viv, user3_viv}

        active_at_a = rm_not_active_at_date(all_users, db["pA"])
        active_at_b = rm_not_active_at_date(all_users, db["pB"])
        active_at_c = rm_not_active_at_date(all_users, db["pC"])
        active_at_d = rm_not_active_at_date(all_users, db["pD"])
        active_at_e = rm_not_active_at_date(all_users, db["pE"])
        active_at_f = rm_not_active_at_date(all_users, db["pF"])

        self.assertEqual(active_at_a, {user1_viv})
        self.assertEqual(active_at_b, {user1_viv, user3_viv})
        self.assertEqual(active_at_c, {user1_viv, user2_viv, user3_viv})
        self.assertEqual(active_at_d, {user2_viv, user3_viv})
        self.assertEqual(active_at_e, {user2_viv})
        self.assertEqual(active_at_f, {user2_viv})

    def test_rm_not_active_at_date_method_everybody_left(self):
        db = get_setup_w_vivienda_3_users_and_periods()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user1_viv = user1.get_vu()
        user3_viv = user3.get_vu()
        user2_viv = user2.get_vu()
        vivienda = db["vivienda"]

        user1_viv.fecha_creacion = db["pA"]
        user1_viv.fecha_abandono = db["pC"]
        user1_viv.estado = "inactivo"
        user1_viv.save()

        user2_viv.fecha_creacion = db["pC"]
        user2_viv.fecha_abandono = db["pD"]
        user2_viv.estado = "inactivo"
        user2_viv.save()

        user3_viv.fecha_creacion = db["pB"]
        user3_viv.fecha_abandono = db["pD"]
        user3_viv.estado = "inactivo"
        user3_viv.save()

        all_users = {user1_viv, user2_viv, user3_viv}

        active_at_a = rm_not_active_at_date(all_users, db["pA"])
        active_at_b = rm_not_active_at_date(all_users, db["pB"])
        active_at_c = rm_not_active_at_date(all_users, db["pC"])
        active_at_d = rm_not_active_at_date(all_users, db["pD"])
        active_at_e = rm_not_active_at_date(all_users, db["pE"])
        active_at_f = rm_not_active_at_date(all_users, db["pF"])

        self.assertEqual(active_at_a, {user1_viv})
        self.assertEqual(active_at_b, {user1_viv, user3_viv})
        self.assertEqual(active_at_c, {user1_viv, user2_viv, user3_viv})
        self.assertEqual(active_at_d, {user2_viv, user3_viv})
        self.assertEqual(active_at_e, set())
        self.assertEqual(active_at_f, set())

    def test_rm_not_active_at_date_method_no_one_has_left(self):
        db = get_setup_w_vivienda_3_users_and_periods()

        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        user1_viv = user1.get_vu()
        user3_viv = user3.get_vu()
        user2_viv = user2.get_vu()
        vivienda = db["vivienda"]

        all_users = {user1_viv, user2_viv, user3_viv}

        active_at_a = rm_not_active_at_date(all_users, db["pA"])
        active_at_b = rm_not_active_at_date(all_users, db["pB"])
        active_at_c = rm_not_active_at_date(all_users, db["pC"])
        active_at_d = rm_not_active_at_date(all_users, db["pD"])
        active_at_e = rm_not_active_at_date(all_users, db["pE"])
        active_at_f = rm_not_active_at_date(all_users, db["pF"])

        self.assertEqual(active_at_a, all_users)
        self.assertEqual(active_at_b, all_users)
        self.assertEqual(active_at_c, all_users)
        self.assertEqual(active_at_d, all_users)
        self.assertEqual(active_at_e, all_users)
        self.assertEqual(active_at_f, all_users)

    def test_compute_balance_method(self):
        db = get_setup_w_vivienda_3_users_and_periods()
        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        vivienda = db["vivienda"]

        actual_total = {user1: 1200, user2: 2000, user3: 1500}
        expected_total = {user1: 900, user2: 2900, user3: 900}

        balance = compute_balance(actual_total, expected_total)

        # result dict should be:
        # {user2: [(user1, 300), (user3, 600)]}
        self.assertEqual(balance.get(user1, None), None)
        self.assertEqual(balance.get(user3, None), None)

        user2_transfers = balance.get(user2, None)
        self.assertNotEqual(user2_transfers, None)
        self.assertEqual(len(user2_transfers), 2)
        self.assertEqual(
            set(user2_transfers),
            {(user1, 300), (user3, 600)}
        )

    def test_compute_balance_method_already_balanced(self):
        db = get_setup_w_vivienda_3_users_and_periods()
        user1 = db["user1"]
        user2 = db["user2"]
        user3 = db["user3"]
        vivienda = db["vivienda"]

        actual_total = {user1: 1200, user2: 2000, user3: 1500}
        expected_total = {user1: 1200, user2: 2000, user3: 1500}

        balance = compute_balance(actual_total, expected_total)

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
            user4: 9000
        }
        expected_total = {
            user1: 3000,
            user2: 2500,
            user3: 7000,
            user4: 5000
        }

        balance = compute_balance(actual_total, expected_total)

        self.assertEqual(balance.get(user2, None), None)
        self.assertEqual(balance.get(user4, None), None)

        user1_transfers = balance.get(user1, None)
        self.assertNotEqual(user1_transfers, None)
        self.assertEqual(len(user1_transfers), 1)

        user3_transfers = balance.get(user3, None)
        self.assertNotEqual(user3_transfers, None)
        self.assertEqual(len(user3_transfers), 2)

        self.assertEqual(sum([m for u, m in user1_transfers]), 1000)
        self.assertEqual(sum([m for u, m in user3_transfers]), 5500)
