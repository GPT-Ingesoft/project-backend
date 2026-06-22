from django.core.management.base import BaseCommand

from information_app.services.preventive_services import PreventiveMaintenanceServices


class Command(BaseCommand):
    help = 'Envía notificaciones de mantenimientos preventivos próximos.'

    def handle(self, *args, **options):
        result = PreventiveMaintenanceServices().notify_upcoming()
        self.stdout.write(
            self.style.SUCCESS(
                f"Notificados: {len(result['notified_ids'])}. "
                f"Sin destinatarios: {len(result['skipped_without_recipients'])}."
            )
        )
