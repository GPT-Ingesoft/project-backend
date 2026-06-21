from django.db.models import (
    Avg,
    Case,
    Count,
    DurationField,
    ExpressionWrapper,
    F,
    IntegerField,
    Value,
    When,
)
from django.utils import timezone
from information_app.models import Equipo, Notificacion, Solicitud
from information_app.repositories.repository_utils import BaseRepository

class AdminRepository(BaseRepository):
    def get_model(self):
        return Equipo

    # ── Query operations ─────────────────────────────────────────

    def get_notification_history(self):
        return (
            Notificacion.objects
            .select_related('solicitud')
            .prefetch_related('destinatarios')
            .order_by('-fecha_envio')
        )

    def get_notification_by_id(self, notification_id: int):
        return (
            Notificacion.objects
            .select_related('solicitud')
            .prefetch_related('destinatarios')
            .filter(id=notification_id)
            .first()
        )

    @staticmethod
    def get_active_requests():
        priority_order = Case(
            When(prioridad='alta', then=Value(0)),
            When(prioridad='media', then=Value(1)),
            When(prioridad='baja', then=Value(2)),
            default=Value(3),
            output_field=IntegerField(),
        )
        return (
            Solicitud.objects
            .select_related('equipo')
            .filter(estado__in=('pendiente', 'en_proceso'))
            .annotate(orden_prioridad=priority_order)
            .order_by('orden_prioridad', 'fecha_creacion')
        )

    def get_failure_report(self):
        return (
            self.get_model()
            .annotate(total_fallas=Count('solicitudes'))
            .filter(total_fallas__gt=0)
            .order_by('-total_fallas')
            .values('id', 'nombre', 'codigo_inventario', 'ubicacion', 'estado', 'total_fallas')
        )

    def get_repair_time_report(self):
        return (
            self.get_model()
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

    def get_out_of_service_equipment(self, umbral_dias: int):
        ahora = timezone.now()
        equipos = list(
            self.get_model()
            .filter(estado='fuera_de_servicio', fecha_baja__isnull=False)
            .values(
                'id', 'nombre', 'codigo_inventario',
                'ubicacion', 'estado', 'fecha_baja',
                'motivo_baja'
            )
        )
        resultado = []
        for equipo in equipos:
            dias_inactivo = (ahora - equipo['fecha_baja']).days
            if dias_inactivo > umbral_dias:
                equipo['dias_inactivo'] = dias_inactivo
                resultado.append(equipo)
        return sorted(resultado, key=lambda e: e['dias_inactivo'], reverse=True)

    def get_active_equipment(self):
        return (
            self.get_model()
            .filter(estado__in=('operativo', 'en_mantenimiento'))
            .order_by('nombre')
            .values('id', 'nombre', 'ubicacion', 'estado')
        )
