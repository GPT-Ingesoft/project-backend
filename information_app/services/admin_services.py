from ..repositories.admin_repository import AdminRepository

UMBRAL_DIAS_DEFAULT = 30


class AdminServices:
    def __init__(self):
        self.repo = AdminRepository()

    # ── RF_47: Historial de notificaciones ────────────────────────────────────

    def get_notification_history(self) -> list:
        return [self._format_notification(n) for n in self.repo.get_notification_history()]

    # ── RF_50: Reporte de fallas ──────────────────────────────────────────────

    def get_failure_report(self) -> list:
        return [self._format_failure(e) for e in self.repo.get_failure_report()]

    # ── RF_51: Reporte de tiempos de reparación ───────────────────────────────

    def get_repair_time_report(self) -> list:
        return [self._format_repair_time(e) for e in self.repo.get_repair_time_report()]

    # ── RF_52: Reporte de equipos fuera de servicio ───────────────────────────

    def get_out_of_service_equipment_report(self, umbral_dias) -> dict:
        try:
            umbral = int(umbral_dias)
            if umbral < 0:
                raise ValueError()
        except (TypeError, ValueError):
            raise ValueError(
                f"El parámetro 'umbral_dias' debe ser un número entero positivo. "
                f"Valor recibido: '{umbral_dias}'."
            )
        equipos = self.repo.get_out_of_service_equipment_report(umbral)
        return {
            'umbral_dias': umbral,
            'total':       len(equipos),
            'equipos':     [self._format_out_of_service(e) for e in equipos],
        }

    # ── RF_53: Equipos activos ────────────────────────────────────────────────

    def get_active_equipment(self) -> list:
        return [self._format_active_equipment(e) for e in self.repo.get_active_equipment()]

    # ── Formatters ─────────────────────────────────────────────────────────────

    @staticmethod
    def _format_notification(n) -> dict:
        return {
            'id':           n.id,
            'tipo':         n.get_tipo_display(),
            'mensaje':      n.mensaje,
            'fecha_envio':  n.fecha_envio.isoformat(),
            'solicitud_id': n.solicitud.id if n.solicitud else None,
            'destinatarios': [
                {'id': u.id, 'nombre': u.nombre, 'correo': u.correo}
                for u in n.destinatarios.all()
            ],
        }

    @staticmethod
    def _format_failure(e) -> dict:
        return {
            'id':                e['id'],
            'nombre':            e['nombre'],
            'codigo_inventario': e['codigo_inventario'],
            'ubicacion':         e['ubicacion'],
            'estado':            e['estado'],
            'total_fallas':      e['total_fallas'],
        }

    @staticmethod
    def _format_repair_time(e) -> dict:
        promedio = e['promedio_horas']
        total_horas = round(promedio.total_seconds() / 3600, 2) if promedio else None
        return {
            'id':                            e['id'],
            'nombre':                        e['nombre'],
            'codigo_inventario':             e['codigo_inventario'],
            'ubicacion':                     e['ubicacion'],
            'promedio_horas_reparacion':     total_horas,
        }

    @staticmethod
    def _format_out_of_service(e) -> dict:
        return {
            'id':                e['id'],
            'nombre':            e['nombre'],
            'codigo_inventario': e['codigo_inventario'],
            'ubicacion':         e['ubicacion'],
            'estado':            e['estado'],
            'fecha_baja':        e['fecha_baja'].isoformat() if e['fecha_baja'] else None,
            'motivo_baja':       e['motivo_baja'],
            'dias_inactivo':     e['dias_inactivo'],
        }

    @staticmethod
    def _format_active_equipment(e) -> dict:
        return {
            'id':        e['id'],
            'nombre':    e['nombre'],
            'ubicacion': e['ubicacion'],
            'estado':    e['estado'],
        }
