from django.conf import settings
from django.core.mail import send_mass_mail
from django.db import transaction

from information_app.repositories.notification_repository import NotificationRepository


class NotificationServices:
    def __init__(self):
        self.repository = NotificationRepository()

    def notify_request_status_change(
        self,
        request,
        previous_status: str,
        reason: str = '',
    ) -> None:
        if previous_status == request.estado:
            return

        recipients = self._request_recipients(request)
        message = (
            f"La solicitud de mantenimiento #{request.id} cambió de "
            f"'{previous_status}' a '{request.estado}'."
        )
        if reason:
            message = f"{message} Motivo: {reason}"
        self._record_and_schedule_email(
            subject=f"Actualización de solicitud #{request.id}",
            message=message,
            notification_type='cambio_estado',
            recipients=recipients,
            request=request,
        )
    
    def notify_technician_assignment(self, request, technicians) -> None:
        recipients = [t.usuario for t in technicians]
        technician_names = ', '.join(t.usuario.nombre for t in technicians)
        message = (
            f"Has sido asignado junto con {technician_names} a la solicitud de "
            f"mantenimiento #{request.id} para el equipo '{request.equipo.nombre}'."
            if len(technicians) > 1
            else
            f"Has sido asignado a la solicitud de mantenimiento #{request.id} "
            f"para el equipo '{request.equipo.nombre}'."
        )
        self._record_and_schedule_email(
            subject=f"Asignación a solicitud #{request.id}",
            message=message,
            notification_type='asignacion_tecnico',
            recipients=recipients,
            request=request,
        )

    def notify_preventive_maintenance(self, maintenance, recipients) -> None:
        message = (
            f"Se aproxima el mantenimiento preventivo del equipo "
            f"'{maintenance.equipo.nombre}', programado para "
            f"{maintenance.fecha_programada.isoformat()}."
        )
        self._record_and_schedule_email(
            subject=f"Mantenimiento preventivo: {maintenance.equipo.nombre}",
            message=message,
            notification_type='mantenimiento_preventivo',
            recipients=recipients,
        )

    def _record_and_schedule_email(  # pylint: disable=too-many-arguments
        self,
        *,
        subject: str,
        message: str,
        notification_type: str,
        recipients,
        request=None,
    ) -> None:
        unique_recipients = self.get_unique_active_recipients(recipients)
        if not unique_recipients:
            raise ValueError("No hay destinatarios activos con correo para la notificación.")

        self.repository.create_notification(
            message=message,
            notification_type=notification_type,
            recipients=unique_recipients,
            request=request,
        )
        emails = [user.correo for user in unique_recipients]
        transaction.on_commit(
            lambda: self._send_individual_emails(subject, message, emails)
        )

    @staticmethod
    def _request_recipients(request):
        recipients = [request.usuario]
        recipients.extend(
            assignment.tecnico.usuario
            for assignment in request.asignaciones.select_related('tecnico__usuario')
            .filter(activa=True)
        )
        return recipients

    @staticmethod
    def get_unique_active_recipients(recipients):
        unique = {}
        for user in recipients:
            if user and user.activo and user.correo:
                unique[user.id] = user
        return list(unique.values())

    @staticmethod
    def _send_individual_emails(subject: str, message: str, emails) -> None:
        messages = [
            (subject, message, settings.DEFAULT_FROM_EMAIL, [email])
            for email in emails
        ]
        send_mass_mail(messages, fail_silently=False)
