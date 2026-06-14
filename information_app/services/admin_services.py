from ..repositories.admin_repository import AdminRepository

UMBRAL_DIAS_DEFAULT = 30


class AdminServices:
    def __init__(self):
        self.repo = AdminRepository()

    # ── RF_47: Historial de notificaciones ────────────────────────────────────

    def get_historial_notificaciones(self) -> list:
        return [self._format_notificacion(n) for n in self.repo.get_historial_notificaciones()]

    # ── RF_50: Reporte de fallas ──────────────────────────────────────────────

    def get_reporte_fallas(self) -> list:
        return [self._format_falla(e) for e in self.repo.get_reporte_fallas()]

    # ── RF_51: Reporte de tiempos de reparación ───────────────────────────────

    def get_reporte_tiempos_reparacion(self) -> list:
        return [self._format_tiempo_reparacion(e) for e in self.repo.get_reporte_tiempos_reparacion()]

    # ── RF_52: Reporte de equipos fuera de servicio ───────────────────────────

    def get_reporte_equipos_fuera_de_servicio(self, umbral_dias) -> dict:
        try:
            umbral = int(umbral_dias)
            if umbral < 0:
                raise ValueError()
        except (TypeError, ValueError):
            raise ValueError(
                f"El parámetro 'umbral_dias' debe ser un número entero positivo. "
                f"Valor recibido: '{umbral_dias}'."
            )
        equipos = self.repo.get_equipos_fuera_de_servicio(umbral)
        return {
            'umbral_dias': umbral,
            'total':       len(equipos),
            'equipos':     [self._format_fuera_de_servicio(e) for e in equipos],
        }

    # ── RF_53: Equipos activos ────────────────────────────────────────────────

    def get_equipos_activos(self) -> list:
        return [self._format_equipo_activo(e) for e in self.repo.get_equipos_activos()]

    # ── Formatters ─────────────────────────────────────────────────────────────

    @staticmethod
    def _format_notificacion(n) -> dict:
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
    def _format_falla(e) -> dict:
        return {
            'id':                e['id'],
            'nombre':            e['nombre'],
            'codigo_inventario': e['codigo_inventario'],
            'ubicacion':         e['ubicacion'],
            'estado':            e['estado'],
            'total_fallas':      e['total_fallas'],
        }

    @staticmethod
    def _format_tiempo_reparacion(e) -> dict:
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
    def _format_fuera_de_servicio(e) -> dict:
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
    def _format_equipo_activo(e) -> dict:
        return {
            'id':        e['id'],
            'nombre':    e['nombre'],
            'ubicacion': e['ubicacion'],
            'estado':    e['estado'],
        }
