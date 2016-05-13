# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from .helper_functions.balance_functions import *


# helper functions


def get_current_year_month_obj():
    """
    Returns the current YearMonth period.
    If the YearMonth doesn't exist, it creates it.
    :return: YearMonth
    """
    today = timezone.now()
    year_month, created = YearMonth.objects.get_or_create(
        year=today.year, month=today.month)
    return year_month


def get_current_year_month():
    """
    Returns the current YearMonth period's ID field.
    If it doesn't exist, it creates it.
    :return: Integer
    """
    return get_current_year_month_obj().id


def get_default_estado_gasto():
    """
    Returns the "id" field of an instance of EstadoGasto with value
    "pendiente". If it doesn't exist, it creates it first.
    :return: Integer
    """
    estado_gasto, __ = EstadoGasto.objects.get_or_create(
        estado="pendiente")
    return estado_gasto.id


def get_paid_state_gasto():
    """
    Returns an instance of EstadoGasto with value "pagado".
    If it doesn't exist, it creates it first.
    :return: EstadoGasto
    """
    return EstadoGasto.objects.get_or_create(estado="pagado")[0]


def get_pending_state_gasto():
    """
    Returns an instance of EstadoGasto with value "pendiente".
    If it doesn't exist, it creates it first.
    :return: EstadoGasto
    """
    return EstadoGasto.objects.get_or_create(estado="pendiente")[0]


def get_pending_confirmation_state_gasto():
    """
    Returns an instance of EstadoGasto with value "pendiente_confirmacion".
    If it doesn't exist, it creates it first.
    :return: EstadoGasto
    """
    return EstadoGasto.objects.get_or_create(
        estado="pendiente_confirmacion")[0]


def get_default_others_categoria():
    """
    Returns the default Categoria for "Other" Gasto instances. Gastos
    with a hidden Categoria are shown as if they belonged to this Categoria
    :return: Categoria
    """
    return Categoria.objects.get_or_create(nombre="Otros", vivienda=None)[0]


class ProxyUser(User):
    """
    This is used to add methods to the default django User class
    without altering it
    """

    class Meta:
        proxy = True

    def get_vu(self):
        """
        Returns the user's current active Vivienda, or None if it does not have
        one.
        :return: ViviendaUsuario
        """
        return ViviendaUsuario.objects.filter(
            user=self,
            estado="activo").first()

    def has_vivienda(self):
        """
        Returns True if the user has an active Vivienda.
        Otherwise, it returns False.
        :return: Boolean
        """
        return ViviendaUsuario.objects.filter(
            user=self,
            estado="activo").exists()

    def leave(self):
        """
        Changes the state of the related ViviendaUsuario to "inactivo",
        and sets the "fecha_abandono" as the current datetime.
        If the user doesn't currently have a Vivienda, returns False and
        does nothing.
        :return: Boolean
        """
        if self.has_vivienda():
            return self.get_vu().leave()
        return False

    def get_vivienda(self):
        """
        Returns the active Vivienda of the user, or None if it doesn't
        have any.
        :return: Vivienda
        """
        vivienda_usuario = self.get_vu()
        if vivienda_usuario is not None:
            return vivienda_usuario.vivienda
        else:
            return None

    def get_roommates(self):
        """
        Returns a list of all active members of the Vivienda,
        including the User that calls the method.
        If there's no active Vivienda, returns None
        :return: QuerySet( ViviendaUsuario )
        """
        return ViviendaUsuario.objects.filter(
            vivienda=self.get_vivienda(),
            estado="activo")

    def get_roommates_users(self):
        """
        Returns a QuerySet with all User instances that have a related
        active ViviendaUsuario
        :return: QuerySet( User )
        """
        roommates = self.get_roommates().values("user")
        return User.objects.filter(id__in=roommates).exclude(id=self.id)

    def get_invites(self):
        """
        Returns a Tuple consisting of:
        - QuerySet with pending invites the user has received, or None
        - QuerySet with pending invites the user has sent, or None
        :return: Pair( QuerySet( Invitacion ), QuerySet( Invitacion ) )
        """
        invites_in = Invitacion.objects.filter(
            invitado=self, estado="pendiente")
        invites_out = Invitacion.objects.filter(
            invitado_por__user=self, estado="pendiente")
        return invites_in, invites_out

    def sent_invite(self, invite):
        """
        Returns True if the given Invite was sent by the User, or False
        otherwise.
        :param invite: Invitacion
        :return: Boolean
        """
        return invite.invitado_por.user == self

    def go_on_vacation(self,
                       start_date=timezone.now().date(),
                       end_date=timezone.now().date() + timezone.timedelta(
                           weeks=9999)):
        """
        If the user is not already on vacation, creates a new instance of
        UserIsOut with this user's ViviendaUsuario, the current date for
        the "fecha_inicio" field and the given end_date parameter for
        the "fecha_fin" field.
        If there are no errors, returns the newly created UserIsOut, and
        a message saying everything went well.
        If there were errors, it does nothing and returns False plus a
        message with the error.
        :param start_date: Date
        :param end_date: Date
        :return: Pair( UserIsOut, String )
        """
        if self.has_vivienda():
            if start_date > end_date:
                return (
                    False,
                    "La fecha final debe ser posterior a la fecha inicial.")

            # check that it doesn't overlap with existing UserIsOut related
            # to this user. Logic was taken from Charles Bretana's
            # answer in SO:
            # http://stackoverflow.com/a/325964
            for vac in UserIsOut.objects.filter(
                    vivienda_usuario__user=self,
                    vivienda_usuario__estado="activo"):
                vac_starts_early = vac.fecha_inicio <= end_date
                vac_ends_late = vac.fecha_fin >= start_date
                if (vac_starts_early) and (vac_ends_late):
                    return (
                        False,
                        """
                        ¡Las fechas indicadas topan con otra salida programada!
                        """)
            user_is_out = UserIsOut.objects.create(
                vivienda_usuario=self.get_vu(),
                fecha_fin=end_date,
                fecha_inicio=start_date)

            return user_is_out, "¡Salida creada correctamente!"
        return None, "Debe pertenecer a una vivienda para crear una salida"

    def update_vacation(self, vacation, start_date=None, end_date=None):
        """
        Checks that the new period is a valid one. If
        it's not, returns False and an error message. If it is valid,
        changes the given fields with the given values.
        If the user only provides one of the fields, only that field is
        changed.
        :param vacation: UserIsOut
        :param start_date: Date
        :param end_date: Date
        :return: Pair( UserIsOut, String )
        """
        if start_date is None and end_date is None:
            return False, "Debe especificar al menos una de las fechas."
        if end_date is not None:
            vacation.fecha_fin = end_date
        if start_date is not None:
            vacation.fecha_inicio = start_date

        if vacation.fecha_inicio > vacation.fecha_fin:
            return (
                False,
                "La fecha final debe ser posterior a la fecha inicial.")

        for vac in UserIsOut.objects.exclude(id=vacation.id).filter(
                vivienda_usuario__user=self,
                vivienda_usuario__estado="activo"):
            vac_starts_early = vac.fecha_inicio <= vacation.fecha_fin
            vac_ends_late = vac.fecha_fin >= vacation.fecha_inicio
            if vac_starts_early and vac_ends_late:
                return (
                    None,
                    "¡Las fechas indicadas topan con otra salida programada!")

        vacation.save()
        return vacation, "¡Vacación actualizada!"

    def is_out(self):
        """
        Returns True if today's date falls within the range of any
        UserIsOut instance related to this user's ViviendaUsuario.
        If this doesn't happen, or if the user doesn't have a Vivienda,
        returns False.
        :return: Boolean
        """
        if not self.has_vivienda():
            return False
        today = timezone.now().date()
        return UserIsOut.objects.filter(
            vivienda_usuario=self.get_vu(),
            fecha_inicio__lte=today,
            fecha_fin__gte=today).exists()

    def transfer(self, user, monto):
        """
        If the given User and this User belong to the same Vivienda, and both
        Users are active in this Vivienda, this method creates 2 new
        Gasto instances with a paid state and Categoria "Transferencia", and
        returns a tuple with both new Gastos.

        The first Gasto has a positive "monto" field equal to the given monto,
        and is linked to this User (self).
        The second Gasto has a NEGATIVE "monto" field equal to -1 times the
        given monto, and is linked to the given User (parameter).
        This way, this User effectively "transferred" a given monto to the
        given User.
        :param user: User
        :param monto: Integer
        :return: Pair( Gasto, Gasto )
        """
        users_have_vivienda = self.has_vivienda() and user.has_vivienda()
        users_are_roommates = self.get_vivienda() == user.get_vivienda()
        user_is_self = self == user
        monto_is_positive = monto > 0
        is_valid_transfer = (users_have_vivienda and
                             users_are_roommates and
                             not user_is_self and
                             monto_is_positive)

        if is_valid_transfer:
            transfer_categoria, __ = Categoria.objects.get_or_create(
                nombre="Transferencia",
                vivienda=self.get_vivienda(),
                is_transfer=True)

            self_vu = self.get_vu()
            transfer_pos = Gasto.objects.create(
                monto=monto,
                creado_por=self_vu,
                categoria=transfer_categoria)
            self_vu.pay(transfer_pos)

            user_vu = user.get_vu()
            transfer_neg = Gasto.objects.create(
                monto=monto * -1,
                creado_por=user_vu,
                categoria=transfer_categoria)
            user_vu.pay(transfer_neg)
            return (transfer_pos, transfer_neg)
        # user can't transfer
        return (None, None)


class Vivienda(models.Model):

    alias = models.CharField(max_length=200)

    def add_global_items(self):
        """
        For each global Item (an Item with no related Vivienda),
        creates an Item instance with that Items fields,
        but with a foreign key to this Vivienda.
        If the global item already exists, it doesn't create it again.
        """
        global_items = Item.objects.filter(vivienda=None)
        for item in global_items:
            Item.objects.get_or_create(
                nombre=item.nombre,
                unidad_medida=item.unidad_medida,
                descripcion=item.descripcion,
                vivienda=self)

    def get_active_users(self):
        """
        Returns all currently active ViviendaUsuario instances in the Vivienda
        :return: QuerySet( ViviendaUsuario )
        """
        return ViviendaUsuario.objects.filter(
            vivienda=self,
            estado="activo"
        )

    def get_gastos_pendientes(self):
        """
        Returns a QuerySet with the Gastos associated with the Vivienda,
        and with a pending state
        :return: QuerySet( Gasto )
        """
        return Gasto.objects.filter(
            creado_por__vivienda=self,
            estado=get_pending_state_gasto(),
            categoria__is_transfer=False)

    def get_pending_confirmation_gastos(self):
        """
        Returns a QuerySet with the Gastos associated with the Vivienda,
        and with a pending_confirmation state
        :return: QuerySet( Gasto )
        """
        return Gasto.objects.filter(
            creado_por__vivienda=self,
            estado=get_pending_confirmation_state_gasto())

    def get_gastos_pagados(self):
        """
        Returns a QuerySet with the Gastos associated with the Vivienda,
        and with a paid state.
        :return: QuerySet( Gasto )
        """
        return Gasto.objects.filter(
            creado_por__vivienda=self,
            estado=get_paid_state_gasto(),
            categoria__is_transfer=False)

    def get_categorias(self):
        """
        Returns a QuerySet with all Categoria objects related to the Vivienda
        that are not hidden
        :return: QuerySet( Categoria )
        """
        return Categoria.objects.filter(
            vivienda=self,
            hidden=False,
            is_transfer=False)

    def get_items(self):
        """
        Returns a QuerySet with all Items related to this Vivienda
        :return: QuerySet( Item )
        """
        return Item.objects.filter(vivienda=self)

    def get_all_vivienda_categorias_with_is_hidden_field(self):
        """
        Returns a QuerySet with all Categoria objects related to the Vivienda,
        including the hidden Categoria instances
        :return: QuerySet( Categoria )
        """
        return Categoria.objects.filter(vivienda=self, is_transfer=False)

    def get_hidden_total(self, year_month):
        """
        Returns the sum of all Gastos' montos with a Categoria that's
        hidden
        :param year_month: YearMonth
        :return: Integer
        """
        montos = Gasto.objects.filter(
            creado_por__vivienda=self,
            year_month=year_month,
            categoria__vivienda=self,
            categoria__is_transfer=False,
            categoria__hidden=True,
            estado__estado="pagado").values("monto")
        total = 0
        for d in montos:
            total += d["monto"]
        return total

    def get_total_expenses_categoria_period(self, categoria, year_month):
        """
        Returns the total sum of all Gastos made during the given YearMonth
        for the given Categoria in this Vivienda. If the Categoria is the
        default "other" Categoria, it takes into account that Categoria, plus
        all hidden Categorias related to the Vivienda.
        :param categoria: Categoria
        :param year_month: YearMonth
        :return: Integer
        """
        categoria = Categoria.objects.get(
            nombre=categoria,
            vivienda=self)
        if categoria.nombre == get_default_others_categoria().nombre:
            # TODO it's not adding the Gastos with "Otros" as categoria,
            # because it's just adding up the Categorias that are hidden,
            # and "Otros" is not always hidden!
            return self.get_hidden_total(year_month)
        if categoria.is_hidden():
            return 0
        montos = Gasto.objects.filter(
            creado_por__vivienda=self,
            year_month=year_month,
            categoria=categoria,
            estado__estado="pagado").values("monto")
        total = 0
        for d in montos:
            total += d["monto"]
        return total

    def get_total_expenses_period(self, year_month):
        """
        Returns the sum of all Gastos made during the given YearMonth
        regardless of Categoria
        :param year_month: YearMonth
        :return: Integer
        """
        montos = Gasto.objects.filter(
            creado_por__vivienda=self,
            year_month=year_month,
            estado__estado="pagado",
            categoria__is_transfer=False).values("monto")
        total = 0
        for d in montos:
            total += d["monto"]
        return total

    def get_transferencias(self):
        """
        Returns all Gasto instances that:
        - it's Categoria's is_transfer field is True
        - were created by active users
        :return: QuerySet( Gasto )
        """
        return Gasto.objects.filter(
            categoria__is_transfer=True,
            creado_por__vivienda=self,
            creado_por__estado="activo")

    def add_categoria(self, nombre):
        """
        Takes a String representing the name of a new custom Categoria
        the user wants to create. If there's no Categoria with that name,
        a new one is created using the user's Vivienda and the given String
        as the Categoria's "nombre" field.
        Returns a tuple (Categoria, String):
        - the first element is the newly created Categoria, or None
        if there was any error creating it
        - the String is a message explaining what happened (it
        failed for some reason / it finished successfully)
        :param nombre: String
        :return: Pair( Categoria, String)
        """
        categoria, created = Categoria.objects.get_or_create(
            nombre=nombre,
            vivienda=self)
        if not created and categoria.is_global():
            # it's trying to override a global categoria
            return (None,
                    "El nombre ingresado corresponde a una categoría global")
        if created:
            return (categoria, "¡Categoría agregada!")
        return (None, "La categoría ya esta asociada a su vivienda")

    def get_vivienda_global_categorias(self):
        """
        Returns the global Categorias related to this Vivienda
        :return: QuerySet( Categoria )
        """
        global_cats = Categoria.objects.filter(vivienda=None).values("nombre")
        this_viv_global = Categoria.objects.filter(
            vivienda=self,
            nombre__in=global_cats)
        return this_viv_global

    def get_vivienda_custom_categorias(self):
        """
        Returns the custom Categorias related to this Vivienda
        :return: QuerySet( Categoria )
        """
        global_cats = Categoria.objects.filter(vivienda=None).values("nombre")
        custom_cats = Categoria.objects.filter(
            Q(vivienda=self) & ~Q(nombre__in=global_cats))
        return custom_cats

    def get_vacations_after_date(self, date):
        """
        Returns all UserIsOut instances that:
        - happened after the given date, ie, the end date comes
        after the given date (read *NOTE*)
        - is related to a vivienda_usuario related to this Vivienda

        *NOTE*: since the "fecha_fin" field always comes after the
        "fecha_inicio" field, it suffices to say that if the "fecha_fin"
        comes after the given date, the vacation should be returned.
        :param date: Date
        :return: QuerySet( UserIsOut )
        """

        # select_related so that database is not hit again when asking for
        # vivienda_usuario's user
        return UserIsOut.objects.filter(
            vivienda_usuario__vivienda=self,
            fecha_fin__gte=date).select_related("vivienda_usuario__user")

    def get_smart_gasto_dict(self, active_users, all_users, vacations):
        """
        Given a set with currently active ViviendaUsuario instances,
        another Set with all ViviendaUsuario instances related to the
        Vivienda and a set of Vacations, this method returns a dict
        of the form:
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
        :param active_users: Set( ViviendaUsuario )
        :param all_users: Set( ViviendaUsuario )
        :param vacations: Set( UserIsOut )
        :return: Dict(
            Gasto : Pair( Set(ViviendaUsuario), Set(ViviendaUsuario) )
        )
        """
        # get dict "user" -> [UserIsOut1, UserIsOut2, ...]
        vac_dict = dict()
        for vu in all_users:
            vac_dict[vu] = []
        for vacation in vacations:
            vac_dict[vacation.vivienda_usuario].append(vacation)
        gastos = Gasto.objects.filter(
            creado_por__vivienda=self,
            usuario__estado="activo",
            categoria__is_shared=True,
            estado__estado="pagado")

        gastos_users_dict = dict()

        for gasto in gastos:
            should_have_payed_then = gasto.get_responsible_users(
                all_users,
                vac_dict)
            pay_active_today = set.intersection(
                set(active_users),
                should_have_payed_then)
            gastos_users_dict[gasto] = (pay_active_today, should_have_payed_then)

        return gastos_users_dict

    def get_reversed_user_totals_dict(self, gastos_users_dict):
        """
        Converts a dict of the form:
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
        much the user should've spent.

        IMPORTANT Explanation:
        Q: why are the actual totals per user LESS than the "naive" approach
        of just adding up every Gasto payed by each currently active user?

        A: Suppose there was a time when users A and B were sharing expenses,
        but user C was not a part of the Vivienda yet. Furthermore, say B
        left a couple of weeks ago, and is no longer a part of the Vivienda.
        Thus, if A spent money when only A and B were roommates, C should not
        PERCEIVE this Gasto.

        If A was awarded that whole Gasto's monto, then this would unbalance
        the total amounts per user, because this would mean C is ALSO
        responsible for a portion of that Gasto.

        C should perceive that A spent that money at that time, but only half
        of it was meant for himself (because it was shared with B).
        Then, user A should be awarded part of that expense: the portion of it
        that was shared with users that are still active TODAY.

        Let's look at another example: suppose there was a time when users A,
        B and C shared the Vivienda, and A made a Gasto for 1000. However,
        today only A, C and D share the Vivienda. This would mean that 2/3 of
        that Gasto's monto should be added to the total of A.
        Why?
        Because A and C (2 users) perceived that Gasto, but it was
        also split with B at the time (3 users), meaning it was split
        into 3 parts. However, only 2 of those 3 users are still active
        => only 2/3 parts of the monto should be added to A.
        The other 1/3 part is assumed to have been balanced with B before
        she/he left.
        :param gastos_users_dict: Dict(
            Gasto : Pair( Set(ViviendaUsuario), Set(ViviendaUsuario) )
        )
        :return: Pair( Dict(User: Integer), Dict(User: Integer) )
        """
        actual_total_per_user = dict()
        expected_total_per_user = dict()
        active_users = ViviendaUsuario.objects.filter(
            vivienda=self,
            estado="activo")
        for vu in active_users:
            actual_total_per_user[vu] = 0
            expected_total_per_user[vu] = 0
        for gasto in gastos_users_dict:
            today_users, past_users = gastos_users_dict[gasto]
            user_that_payed = gasto.usuario
            shared_portion = len(today_users) / len(past_users)
            share = gasto.monto * shared_portion
            actual_total_per_user[user_that_payed] += share
            for vu in today_users:
                expected_total_per_user[vu] += share / len(today_users)

        return actual_total_per_user, expected_total_per_user

    def get_smart_totals(self):
        """
        Returns a tuple with:
        - a dict with the actual totals each active user has spent
        - a dict with the expected totals for each active user
        :return: Pair( Dict(User: Integer), Dict(User: Integer) )
        """
        all_users = ViviendaUsuario.objects.filter(
            vivienda=self)
        active_users = all_users.filter(estado="activo")
        # get the earliest user that is still active in the Vivienda
        dates = set()
        for vu in active_users:
            dates.add(vu.fecha_creacion)
        start_date = min(dates)
        vacations = self.get_vacations_after_date(start_date)
        gasto_user_dict = self.get_smart_gasto_dict(
            active_users=active_users,
            all_users=all_users,
            vacations=vacations)

        return self.get_reversed_user_totals_dict(gasto_user_dict)

    def get_disbalance_dict(self):
        """
        Returns a dict of the form:
        {
            User: Integer
        }
        where the Integer represents how much the User ows to other users
        (Integer is negative, meaning he has spent too little), or how much the
        User is owed (if the Integer is positive, meaning he has spent too
        much)
        :return: Dict(User: Integer)
        """
        act, exp = self.get_smart_totals()
        disbalance_dict = dict()
        for user in act:
            diff = act[user] - exp[user]
            if abs(diff)<5:
                diff = 0
            disbalance_dict[user] = diff
        return disbalance_dict

    def get_smart_balance(self):
        """
        Computes the instructions for users to balance out their shared
        expenses
        :return: Dict(User: List( Pair( User, Integer ) )
        """
        (actual_totals,
         expected_totals) = self.get_smart_totals()

        return compute_balance(actual_totals, expected_totals)

    def __str__(self):
        return self.alias


class ViviendaUsuario(models.Model):

    class Meta:
        unique_together = (('vivienda', 'user', 'estado', 'fecha_creacion'),)
    vivienda = models.ForeignKey(Vivienda, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    estado = models.CharField(max_length=200, default="activo")
    fecha_creacion = models.DateField(auto_now_add=True)
    fecha_abandono = models.DateField(null=True, blank=True, default=None)

    def __str__(self):
        return str(self.vivienda) + "__" + str(self.user)

    def leave(self):
        """
        Changes the state of the ViviendaUsuario to "inactivo", and sets the
        "fecha_abandono" as the current datetime, and then returns True.
        If this ViviendaUsuario was not active, does nothing and returns False
        :return: Boolean
        """
        if self.is_active():
            self.estado = "inactivo"
            self.fecha_abandono = timezone.now()
            self.save()
            return True
        return False

    def is_active(self):
        """
        Returns True if the ViviendaUsuario's state is active, or
        False otherwise
        :return: Boolean
        """
        return self.estado == "activo"

    def get_gastos_vivienda(self):
        """
        If the user is active, returns a Tuple with:
        - QuerySet with the Gastos associated with the Vivienda,
        and with a pending state
        - QuerySet with the Gastos associated with the Vivienda,
        and with a paid state

        If the user is not active, returns a Tuple of empty QuerySets
        :return: Pair( QuerySet( Gasto ), QuerySet( Gasto ) )
        """
        if self.is_active():
            return (self.vivienda.get_gastos_pendientes(),
                    self.vivienda.get_gastos_pagados())
        else:
            # returns empty queryset
            empty_queryset = Gasto.objects.none()
            return (empty_queryset, empty_queryset)

    def pay(self, gasto, fecha_pago=timezone.now().date()):
        """
        Sets the state of the given Gasto as "pendiente_confirmacion", and it's
        "usuario" field as the ViviendaUsuario. Also creates a
        ConfirmacionUsuario instance per active user in the Vivienda.
        :param gasto: Gasto
        :param fecha_pago: Date
        """
        gasto.usuario = self
        gasto.fecha_pago = fecha_pago
        ym, __ = YearMonth.objects.get_or_create(
            year=fecha_pago.year,
            month=fecha_pago.month)
        gasto.year_month = ym
        gasto.set_pending_confirmation_state()
        gasto.save()
        for vu in self.vivienda.get_active_users():
            ConfirmacionGasto.objects.create(vivienda_usuario=vu, gasto=gasto)
        # the user that pays immediately confirms the payment
        self.confirm(gasto)

    def confirm(self, gasto):
        """
        Finds a ConfirmacionGasto instance realted to the given Gasto and
        this ViviendaUsuario, and changes it's "confirmed" field to True.
        If, after the change, all ConfirmacionGasto instances related to the
        given Gasto are confirmed, changes the state to the
        confirmed_paid_state
        """
        gasto_confirmation = ConfirmacionGasto.objects.filter(
            gasto=gasto, vivienda_usuario=self).first()
        if gasto_confirmation is not None:
            gasto_confirmation.confirmed = True
            gasto_confirmation.save()
            if not ConfirmacionGasto.objects.filter(
                    gasto=gasto,
                    confirmed=False).exists():
                # all users have confirmed
                gasto.set_confirmed_paid_state()

    def confirm_pay(self, gasto, fecha_pago=timezone.now().date()):
        """
        Sets the state of the given Gasto as "pagado", and it's "usuario" field
        as the ViviendaUsuario.

        This method is used for TESTING purposes, because it skips the
        confirmation phase of paying a Gasto. However, this should never
        happen in the actual application.

        :param gasto: Gasto
        :param fecha_pago: Date
        """
        gasto.usuario = self
        gasto.fecha_pago = fecha_pago
        ym, __ = YearMonth.objects.get_or_create(
            year=fecha_pago.year,
            month=fecha_pago.month)
        gasto.year_month = ym
        estado_gasto, created = EstadoGasto.objects.get_or_create(
            estado="pagado")
        gasto.estado = estado_gasto
        gasto.save()

    def sent_invite(self, invite):
        """
        Returns True if the given Invite was sent by the ViviendaUsuario's
        User, or False otherwise.
        :param invite: Invitacion
        :return: Boolean
        """
        return invite.invitado_por.user == self.user


class UserIsOut(models.Model):

    vivienda_usuario = models.ForeignKey(
        ViviendaUsuario,
        on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()


class Invitacion(models.Model):
    # this key can be null if you invite an account-less user. In this case
    # the invitation is sent to the email.
    invitado = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True)
    invitado_por = models.ForeignKey(ViviendaUsuario, on_delete=models.CASCADE)
    email = models.EmailField()
    estado = models.CharField(max_length=200, default="pendiente")
    # estado es pendiente, rechazada o aceptada

    def __str__(self):
        return str(self.invitado_por) + "__invited__" + str(self.invitado)

    def accept(self):
        """
        Changes the state of the Invitacion to "aceptada" and creates an
        instance of ViviendaUsuario using the Vivienda of the "invitado_por"
        field, and the "invitado" field as the User
        """
        self.estado = "aceptada"
        self.save()
        ViviendaUsuario.objects.create(
            user=self.invitado, vivienda=self.invitado_por.vivienda)

    def reject(self):
        """
        Changes the state of the Invitacion to "rechazada"
        """
        self.estado = "rechazada"
        self.save()

    def is_cancelled(self):
        """
        Returns True if the state of the Invitacion is "cancelada", or
        False otherwise
        :return: Boolean
        """
        return self.estado == "cancelada"

    def cancel(self):
        """
        Changes the state of the Invitacion to "cancelada"
        """
        self.estado = "cancelada"
        self.save()

    def is_invited_user(self, user):
        """
        Returns True if the given User is the one that's being invited
        :param user: User
        :return: Boolean
        """
        return self.invitado == user

    def is_invited_by_user(self, user):
        """
        Returns True if the given user is the one who sent the Invitacion
        :param user: User
        :return: Boolean
        """
        return user.sent_invite(self)


class SolicitudAbandonarVivienda(models.Model):
    creada_por = models.ForeignKey(ViviendaUsuario, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=100)

    def __str__(self):
        return str(self.creada_por) + "__" + str(self.fecha)


class Categoria(models.Model):

    class Meta:
        ordering = ['nombre']
        unique_together = (('nombre', 'vivienda'),)
    nombre = models.CharField(max_length=100)
    vivienda = models.ForeignKey(
        Vivienda,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None)
    hidden = models.BooleanField(default=False)
    is_shared = models.BooleanField(default=True)
    is_shared_on_leave = models.BooleanField(default=True)
    is_transfer = models.BooleanField(default=False)

    def is_global(self):
        """
        Returns True if the Categoria is Global and shared with every Vivienda
        :return: Boolean
        """
        return Categoria.objects.filter(
            vivienda=None,
            nombre=self.nombre).exists()

    def is_hidden(self):
        """
        Returns it's hidden field's boolean value
        :return: Boolean
        """
        return self.hidden

    def hide(self):
        """
        If the Categoria is not hidden, changes this Categoria's hidden
        field to True and returns True. If it's already hidden, returns
        False and does nothing
        :return: Boolean
        """
        if not self.is_hidden():
            self.hidden = True
            self.save()
            return True
        return False

    def show(self):
        """
        If this Categoria is not hidden, it returns False. If it's
        hidden, changes the it's hidden field to False
        :return: Boolean
        """
        if self.is_hidden():
            self.hidden = False
            self.save()
            return True
        return False

    def toggle(self):
        """
        Toggles the hidden field of this Categoria.
        :return: Boolean
        """
        if self.is_hidden():
            return self.show()
        return self.hide()

    def __str__(self):
        return self.nombre


class Item(models.Model):

    class Meta:
        unique_together = ('nombre', 'vivienda')

    nombre = models.CharField(max_length=255)
    descripcion = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default="")
    unidad_medida = models.CharField(max_length=255, default="unidad")
    vivienda = models.ForeignKey(
        Vivienda,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None)

    def __str__(self):
        return str(self.nombre) + " (" + str(self.unidad_medida) + ")"

    def is_in_lista(self, lista):
        """
        Returns True if the Item is in the given ListaCompras, or
        False otherwise
        :param lista: ListaCompras
        :return: Boolean
        """
        return ItemLista.objects.filter(item=self, lista=lista).exists()


class YearMonth(models.Model):

    class Meta:
        unique_together = (('year', 'month'),)
    year = models.IntegerField()
    month = models.IntegerField()

    def get_next_period(self):
        """
        Returns a Tuple of Integers with:
        - the year of the period following this YearMonth
        - the month of the period following this YearMonth
        :return: Pair( Integer, Integer )
        """
        next_month = self.month + 1
        next_year = self.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        return (next_year, next_month)

    def get_prev_period(self):
        """
        Returns a Tuple of Integers with:
        - the year of the period previous to this YearMonth
        - the month of the period previous to this YearMonth
        :return: Pair( Integer, Integer )
        """
        prev_month = self.month - 1
        prev_year = self.year
        if prev_month == 0:
            prev_month = 12
            prev_year -= 1
        return (prev_year, prev_month)

    def __str__(self):
        return str(self.year) + "-" + str(self.month)


class Presupuesto(models.Model):

    class Meta:
        unique_together = (('categoria', 'vivienda', 'year_month'),)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    vivienda = models.ForeignKey(Vivienda, on_delete=models.CASCADE)
    year_month = models.ForeignKey(
        YearMonth, on_delete=models.CASCADE, default=get_current_year_month)
    monto = models.IntegerField(default=0)

    def __str__(self):
        return "".join((
            str(self.vivienda),
            "__",
            str(self.categoria),
            "__",
            str(self.year_month)))

    def get_total_expenses(self):
        """
        Returns the sum of all paid Gastos of the Presupuesto's Categoria in
        the Presupuesto's YearMonth for the Presupuesto's Vivienda
        :return: Integer
        """
        return self.vivienda.get_total_expenses_categoria_period(
            self.categoria,
            self.year_month)


class ListaCompras(models.Model):
    usuario_creacion = models.ForeignKey(
        ViviendaUsuario, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=255, default="pendiente")

    def __str__(self):
        return "".join(
            (str(self.usuario_creacion),
                "__",
                str(self.fecha),
                "__",
                str(self.estado)))

    def get_item_by_name(self, item_name):
        """
        Given an item name, returns the Item instance with that name that is
        related to this Lista's Vivienda
        :param item_name: String
        :return: Item
        """
        return Item.objects.filter(
            nombre=item_name,
            vivienda=self.usuario_creacion.vivienda).first()

    def add_item(self, item, quantity):
        """
        Creates and returns an instance of ItemLista with the given Item and
        quantity, and links it to the ListaCompras.
        If the Item is already in the ListaCompras, it doesn't do anything,
        and returns None.
        :param item: Item
        :param quantity: Integer
        :return: ItemLista
        """
        if item is not None and item.id > 0 and not item.is_in_lista(self):
            new_list_item = ItemLista.objects.create(
                item=item,
                lista=self,
                cantidad_solicitada=quantity)
            return new_list_item
        else:
            return None

    def add_item_by_name(self, item_name, quantity):
        """
        Same as add_item, but receives the Item's name instead of it's id
        :param item_name: String
        :param quantity: Integer
        :return: ItemLista
        """
        item = self.get_item_by_name(item_name)
        return self.add_item(item, quantity)

    def get_items(self):
        """
        Returns a QuerySet with all ItemLista objects linked to this
        ListaCompras.
        :return: QuerySet( ItemLista )
        """
        return ItemLista.objects.filter(lista=self)

    def count_items(self):
        """
        Returns the number of ItemLista objects linked to this ListaCompras.
        :return: Integer
        """
        this_list_items = self.get_items()
        return len(this_list_items)

    def allow_user(self, usuario):
        """
        Returns True if the user is active in the Vivienda of the
        Viviendausuario that created the ListaCompras. Otherwise, it returns
        False.
        :param usuario: User
        :return: Boolean
        """
        vivienda_usuario = usuario.get_vu()
        return (vivienda_usuario is not None and
                self.usuario_creacion.vivienda == vivienda_usuario.vivienda)

    def is_done(self):
        """
        Returns True if the state is "pagada", and the corresponding Gasto of
        the Lista has an is_paid state. Returns False otherwise.
        :return: Boolean
        """
        if self.estado != "pagada":
            return False
        gasto = self.gasto_set.first()
        if gasto is None:
            return False
        return gasto.is_paid()

    def is_pending_confirm(self):
        """
        Returns True if the state of the related Gasto has a pending_confirm
        state. Returns False otherwise.
        :return: Boolean
        """
        gasto = self.gasto_set.first()
        if gasto is not None:
            return gasto.is_pending_confirm()
        return False

    def set_done_state(self):
        """
        If the state is not "pagada", it changes the state to "pagada" and
        returns True. If the state is already "pagada", doesn't do anything
        and returns False.
        :return: Boolean
        """
        if not self.estado == "pagada":
            self.estado = "pagada"
            self.save()
            return True
        return False

    def buy_item(self, item, quantity):
        """
        Changes the state of the ItemLista linked to the given Item and the
        current ListaCompras to "comprado", and sets it's "cantidad_comprada"
        field to the given quantity
        :param item: Item
        :param quantity: Integer
        :return: ItemLista
        """
        il = ItemLista.objects.get(id=item)
        return il.buy(quantity)

    def buy_list(self, item_list, monto_total, vivienda_usuario):
        """
        Receives a list of tuples (item_id, quantity), and changes
        the state of the ItemLista linked to each item_id to "comprado", and
        sets the "cantidad comprada" field to the given quantity.
        Then, changes the state of the ListaCompras to "pagada", and creates
        a new Gasto object linked to this ListaCompras.
        It sets the usuario field of the Gasto with the given
        vivienda_usuario. The Categoria of the Gasto is set to
        "Supermercado".
        Returns the newly created Gasto object.
        :param item_list: List( Pair( Integer, Integer ) )
        :param monto_total: Integer
        :param vivienda_usuario: ViviendaUsuario
        :return: Gasto
        """
        # mark items as bought
        if item_list is None or len(item_list) < 1:
            return None
        for item_id, quantity in item_list:
            self.buy_item(item_id, quantity)
        self.set_done_state()
        # create new Gasto
        nuevo_gasto = Gasto.objects.create(
            monto=monto_total,
            creado_por=vivienda_usuario,
            categoria=Categoria.objects.get_or_create(
                nombre="Supermercado",
                vivienda=vivienda_usuario.vivienda)[0],
            lista_compras=self)
        nuevo_gasto.pay(vivienda_usuario)
        return nuevo_gasto

    def get_gasto(self):
        """
        Returns the Gasto object linked to the ListaCompras.
        If there's no Gasto linked to it, returns None.
        :return: Gasto
        """
        gastos = Gasto.objects.filter(lista_compras=self)
        if len(gastos) == 0 or len(gastos) > 1:
            # TODO raise error
            return None
        else:
            return gastos.first()

    def get_missing_items(self):
        """
        Returns a QuerySet with all ItemLista objects linked to the
        ListaCompras that have a pending state
        :return: QuerySet( ItemLista )
        """
        return ItemLista.objects.filter(lista=self, estado="pendiente")

    def has_missing_items(self):
        """
        Returns True if there's at least 1 ItemLista object with a
        pending state linked to the ListaCompras.
        :return: Boolean
        """
        return len(self.get_missing_items()) > 0

    def rescue_items(self, vivienda_usuario):
        """
        Creates and returns a new ListaComrpas using the pending Items
        form the current ListaCompras. If there are no pending Itemista
        objects, it returns None
        :param vivienda_usuario: ViviendaUsuario
        :return: ListaCompras
        """
        cond1 = self.has_missing_items()
        cond2 = self.count_items() != self.get_missing_items().count()
        if (cond1 and cond2):
            nueva_lista = ListaCompras.objects.create(
                usuario_creacion=vivienda_usuario)
            for item in self.get_missing_items():
                item.lista = nueva_lista
                item.save()
            return nueva_lista

    def discard_items(self):
        """
        Deletes all ItemLista instances with a pending state linked
        to the ListaCompras
        """
        for item in self.get_missing_items():
            item.delete()


class ItemLista(models.Model):

    class Meta:
        unique_together = (('item', 'lista'),)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    lista = models.ForeignKey(ListaCompras, on_delete=models.CASCADE)
    cantidad_solicitada = models.IntegerField()
    cantidad_comprada = models.IntegerField(null=True, blank=True, default=0)
    estado = models.CharField(max_length=255, default="pendiente")

    def __str__(self):
        return "".join((str(self.item),
                        "__",
                        str(self.estado),
                        "__",
                        str(self.lista)))

    def set_done_state(self):
        """
        Changes the state to "comprado"
        """
        self.estado = "comprado"
        self.save()

    def is_pending(self):
        """
        Returns True if the state is "pendiente"
        :return: Boolean
        """
        return self.estado == "pendiente"

    def get_state(self):
        """
        Returns the state
        :return: String
        """
        return self.estado

    def buy(self, quantity):
        """
        Changes the state to "comprado" and sets the cantidad_comprada
        to the given quantity
        :param quantity: Integer
        :return: ItemLista
        """
        if quantity > 0 and self.is_pending():
            self.cantidad_comprada = quantity
            self.set_done_state()
            self.save()
        return self


class EstadoGasto(models.Model):
    estado = models.CharField(max_length=255)

    def __str__(self):
        return str(self.estado)

    def is_pending(self):
        """
        Returns True is the state is "pendiente"
        :return: Boolean
        """
        return self.estado == "pendiente"

    def is_pending_confirm(self):
        """
        Returns True is the state is "pendiente_confirmacion"
        :return: Boolean
        """
        return self.estado == get_pending_confirmation_state_gasto().estado

    def is_paid(self):
        """
        Returns True is the state is "pagado"
        :return: Boolean
        """
        return self.estado == "pagado"


class Gasto(models.Model):
    monto = models.IntegerField()
    creado_por = models.ForeignKey(
        ViviendaUsuario, on_delete=models.CASCADE, related_name="creado_por")
    usuario = models.ForeignKey(
        ViviendaUsuario, on_delete=models.CASCADE, null=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    fecha_creacion = models.DateField(auto_now_add=True)
    fecha_pago = models.DateField(null=True, blank=True)
    year_month = models.ForeignKey(YearMonth,
                                   on_delete=models.CASCADE,
                                   null=True,
                                   blank=True)
    lista_compras = models.ForeignKey(
        ListaCompras, on_delete=models.CASCADE, blank=True, null=True)
    estado = models.ForeignKey(
        EstadoGasto,
        on_delete=models.CASCADE,
        default=get_default_estado_gasto,
        blank=True)

    def __str__(self):
        return "".join((str(self.usuario),
                        "__",
                        str(self.categoria),
                        "__",
                        str(self.year_month)))

    def pay(self, vivienda_usuario, fecha_pago=timezone.now().date()):
        """
        It receives a ViviendaUsuario object and changes the state of the
        Gasto to "pendiente_confirmacion" and the "usuario" field to the given
        ViviendaUsuario.
        :param vivienda_usuario: ViviendaUsuario
        :param fecha_pago: Date
        """
        vivienda_usuario.pay(self, fecha_pago)

    def confirm_pay(self, vivienda_usuario, fecha_pago=timezone.now().date()):
        """
        It receives a ViviendaUsuario object and changes the state of the
        Gasto to "pagado" by the given ViviendaUsuario.
        :param vivienda_usuario: ViviendaUsuario
        :param fecha_pago: Date
        """
        vivienda_usuario.confirm_pay(self, fecha_pago)

    def edit(self, vivienda_usuario, new_monto, new_fecha):
        """
        Changes the fields of the Gasto with the given parameters
        :param vivienda_usuario: ViviendaUsuario
        :param new_monto: Integer
        :param new_fecha: Date
        :return: String
        """
        message = "Gasto editado."
        if not self.is_pending():
            if vivienda_usuario != self.usuario:
                return "No tiene permiso para editar este Gasto"
            # it's either confirmed_payed or pending_confirmation, meaning it
            #  has a not-None "usuario" field
            message = "Gasto editado. Se cambió el estado a pendiente."
            self.fecha_pago = new_fecha
            ym, __ = YearMonth.objects.get_or_create(
                year=new_fecha.year,
                month=new_fecha.month)
            self.year_month = ym
            self.set_pending_confirmation_state()
            for cg in self.confirmaciongasto_set.exclude(
                    vivienda_usuario=self.usuario):
                cg.confirmed = False
                cg.save()
        self.monto = new_monto
        self.save()

        return message

    def is_pending(self):
        """
        Returns True if the state is "pendiente"
        :return: Boolean
        """
        return self.estado.is_pending()

    def is_pending_confirm(self):
        """
        Returns True if the state is "pendiente_confirmacion"
        :return: Boolean
        """
        return self.estado.is_pending_confirm()

    def set_pending_confirmation_state(self):
        """
        Changes the state of the Gasto to "pendiente_confirmacion"
        """
        self.estado = get_pending_confirmation_state_gasto()
        self.save()

    def set_confirmed_paid_state(self):
        """
        Changes the state of the Gasto to "pagado"
        """
        self.estado = get_paid_state_gasto()
        self.save()

    def is_paid(self):
        """
        Returns True if the state is "pagado"
        :return: Boolean
        """
        return self.estado.is_paid()

    def allow_user(self, user):
        """
        Returns True if the User is active in the Vivienda linked
        to the Gasto
        :param user: User
        :return: Boolean
        """
        return (user.has_vivienda() and
                user.get_vivienda() == self.creado_por.vivienda)

    def get_responsible_users(self, all_users, vac_dict):
        """
        Returns all users that were supposed to pay for this Gasto.
        :param all_users: Set( ViviendaUsuario )
        :param vac_dict: Dict( ViviendaUsuario -> List( UserIsOut ) )
        :return: Set( ViviendaUsuario )
        """
        pay_date = self.fecha_pago
        # users active at the time that should have payed
        share_holders = rm_not_active_at_date(
            all_users,
            pay_date)
        if not self.categoria.is_shared_on_leave:
            share_holders = rm_users_out_at_date(
                share_holders,
                vac_dict,
                pay_date)
        # make sure the user that payed is always responsible
        share_holders.add(self.usuario)
        return share_holders

    def get_confirmed_users(self):
        """
        Returns all ViviendaUsuarios who have already confirmed this Gasto
        :return: List( Dict( "vivienda_usuario__user__username" -> String ) )
        """
        return self.confirmaciongasto_set.filter(
            confirmed=True).values("vivienda_usuario__user__username")

    def get_unconfirmed_users(self):
        """
        Returns all ViviendaUsuarios who are yet to confirm this Gasto
        :return: List( Dict( "vivienda_usuario__user__username" -> String ) )
        """
        return self.confirmaciongasto_set.filter(
            confirmed=False).values("vivienda_usuario__user__username")


class ConfirmacionGasto(models.Model):

    class Meta:
        unique_together = ('vivienda_usuario', 'gasto')

    vivienda_usuario = models.ForeignKey(
        ViviendaUsuario,
        on_delete=models.CASCADE)
    confirmed = models.BooleanField(default=False)
    gasto = models.ForeignKey(Gasto, on_delete=models.CASCADE)