# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.utils import timezone

from expenses_manager.models import ViviendaUsuario, Invitacion, UserIsOut, \
    Categoria, Gasto


class ProxyUser(User):
    """This is used to add methods to the default django User class
    without altering it.
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
