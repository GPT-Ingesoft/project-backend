from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField
from django.utils import timezone

from information_app.models import Notificacion, Equipo

class AdminRepository:

    def get_notification_history(self):
        return (
            Notificacion.objects
            .select_related('solicitud')
            .prefetch_related('destinatarios')
            .order_by('-fecha_envio')
        )

    def get_failure_report(self):
        return (
            Equipo.objects
            .annotate(total_fallas=Count('solicitudes'))
            .filter(total_fallas__gt=0)
            .order_by('-total_fallas')
            .values('id', 'nombre', 'codigo_inventario', 'ubicacion', 'estado', 'total_fallas')
        )

    def get_repair_time_report(self):
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

    def get_out_of_service_equipment(self, umbral_dias: int):
        ahora = timezone.now()
        equipos = list(
            Equipo.objects
            .filter(estado='fuera_de_servicio', fecha_baja__isnull=False)
            .values(
                'id', 'nombre', 'codigo_inventario','ubicacion',
                'estado', 'fecha_baja', 'motivo_baja'
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
            Equipo.objects
            .filter(estado__in=('operativo', 'en_mantenimiento'))
            .order_by('nombre')
            .values('id', 'nombre', 'ubicacion', 'estado')
        )
