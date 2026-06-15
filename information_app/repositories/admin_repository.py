from ..models import Notificacion, Equipo
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField
from django.utils import timezone


class AdminRepository:

    # ── RF_47: Historial de notificaciones del más reciente al más antiguo ─────

    def get_notification_history(self):
        # Notificacion.Meta ya define ordering=['-fecha_envio'], lo reforzamos aquí
        return (
            Notificacion.objects
            .select_related('solicitud')
            .prefetch_related('destinatarios')
            .order_by('-fecha_envio')
        )

    # ── RF_50: Equipos ordenados de mayor a menor número de fallas ─────────────

    def get_failure_report(self):
        return (
            Equipo.objects
            .annotate(total_fallas=Count('solicitudes'))
            .filter(total_fallas__gt=0)
            .order_by('-total_fallas')
            .values('id', 'nombre', 'codigo_inventario', 'ubicacion', 'estado', 'total_fallas')
        )

    # ── RF_51: Tiempo promedio de reparación por equipo (solicitudes completadas)

    def get_repair_time_report(self):
        # Solo solicitudes completadas con fecha_cierre registrada
        return (
            Equipo.objects
            .filter(solicitudes__estado='completada', solicitudes__fecha_cierre__isnull=False)
            .annotate(
                promedio_horas=ExpressionWrapper(
                    Avg(F('solicitudes__fecha_cierre') - F('solicitudes__fecha_creacion')),
                    output_field=DurationField(),
                )
            )
            .filter(promedio_horas__isnull=False)
            .order_by('nombre')
            .values('id', 'nombre', 'codigo_inventario', 'ubicacion', 'promedio_horas')
        )

    # ── RF_52: Equipos fuera de servicio con inactividad mayor al umbral ────────

    def get_out_of_service_equipment(self, umbral_dias: int):
        ahora = timezone.now()
        equipos = list(
            Equipo.objects
            .filter(estado='fuera_de_servicio', fecha_baja__isnull=False)
            .values('id', 'nombre', 'codigo_inventario', 'ubicacion', 'estado', 'fecha_baja', 'motivo_baja')
        )
        resultado = []
        for equipo in equipos:
            dias_inactivo = (ahora - equipo['fecha_baja']).days
            if dias_inactivo > umbral_dias:
                equipo['dias_inactivo'] = dias_inactivo
                resultado.append(equipo)
        return sorted(resultado, key=lambda e: e['dias_inactivo'], reverse=True)

    # ── RF_53: Equipos activos para el panel principal ────────────────────────

    def get_active_equipment(self):
        return (
            Equipo.objects
            .filter(estado__in=('operativo', 'en_mantenimiento'))
            .order_by('nombre')
            .values('id', 'nombre', 'ubicacion', 'estado')
        )
