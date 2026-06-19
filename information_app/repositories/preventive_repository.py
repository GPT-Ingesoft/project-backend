from information_app.models import MantenimientoPreventivo, Usuario


class PreventiveMaintenanceRepository:
    @staticmethod
    def get_pending_candidates(now):
        return (
            MantenimientoPreventivo.objects
            .select_related('equipo')
            .prefetch_related('tecnicos__usuario')
            .filter(
                estado='programado',
                notificado_en__isnull=True,
                fecha_programada__gt=now,
            )
            .order_by('fecha_programada')
        )

    @staticmethod
    def get_active_laboratory_technicians():
        return list(
            Usuario.objects.filter(rol='laboratorista', activo=True).order_by('nombre')
        )

    @staticmethod
    def mark_notified(maintenance, notified_at):
        maintenance.notificado_en = notified_at
        maintenance.save(update_fields=['notificado_en'])
