from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from information_app.repositories.preventive_repository import (
    PreventiveMaintenanceRepository,
)
from information_app.services.notification_services import NotificationServices


class PreventiveMaintenanceServices:  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.repository = PreventiveMaintenanceRepository()
        self.notification_service = NotificationServices()

    def notify_upcoming(self, now=None) -> dict:
        current_time = now or timezone.now()
        notified = []
        skipped_without_recipients = []

        for maintenance in self.repository.get_pending_candidates(current_time):
            notification_start = maintenance.fecha_programada - timedelta(
                hours=maintenance.anticipacion_horas
            )
            if current_time < notification_start:
                continue

            result = self._notify_one(maintenance, current_time)
            if result:
                notified.append(maintenance.id)
            else:
                skipped_without_recipients.append(maintenance.id)

        return {
            'notified_ids': notified,
            'skipped_without_recipients': skipped_without_recipients,
        }

    @transaction.atomic
    def _notify_one(self, maintenance, current_time) -> bool:
        recipients = self.repository.get_active_laboratory_technicians()
        recipients.extend(
            technician.usuario
            for technician in maintenance.tecnicos.all()
            if technician.usuario.activo
        )
        if not self.notification_service.get_unique_active_recipients(recipients):
            return False

        self.notification_service.notify_preventive_maintenance(
            maintenance,
            recipients,
        )
        self.repository.mark_notified(maintenance, current_time)
        return True
