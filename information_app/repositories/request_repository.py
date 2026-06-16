
from django.utils import timezone

from information_app.models import Asignacion, Solicitud, Tecnico
from information_app.models import HistorialEstadoSolicitud, Anexo, Adjunto, HorarioAtencion

ESTADOS_VALIDOS = {'pendiente', 'en_proceso', 'completada', 'cancelada'}
ESTADOS_CIERRE  = {'completada', 'cancelada'}


class RequestRepository:

    def get_by_id(self, request_id: int):
        return Solicitud.objects.filter(id=request_id).first()

    def get_technicians_by_ids(self, technician_ids: list[int]):
        return list(
            Tecnico.objects
            .select_related('usuario')
            .filter(usuario_id__in=technician_ids)
        )

    def replace_assigned_technicians(self, request: Solicitud, technicians: list[Tecnico]):
        Asignacion.objects.filter(solicitud=request).update(activa=False)

        assignments = []
        for technician in technicians:
            assignment, _ = Asignacion.objects.update_or_create(
                solicitud=request,
                tecnico=technician,
                defaults={'activa': True},
            )
            assignments.append(assignment)

        return assignments
    # ── Consultas ──────────────────────────────────────────────────────────────

    def get_by_id(self, solicitud_id: int):
        return Solicitud.objects.filter(id=solicitud_id).first()

    def get_lab_schedules(self, laboratorio: str):
        # RF_34
        return (
            HorarioAtencion.objects
            .filter(laboratorio=laboratorio, disponible=True)
            .order_by('dia', 'hora_inicio')
        )

    def get_laboratories(self):
        # RF_34
        return (
            HorarioAtencion.objects
            .values_list('laboratorio', flat=True)
            .distinct()
            .order_by('laboratorio')
        )

    # ── Escritura ──────────────────────────────────────────────────────────────

    def approve(self, solicitud: Solicitud, usuario) -> Solicitud:
        # RF_35: cambia estado a 'en_proceso' y registra historial automáticamente
        estado_anterior = solicitud.estado
        solicitud.estado = 'en_proceso'
        solicitud.save()
        HistorialEstadoSolicitud.objects.create(
            solicitud=solicitud,
            usuario=usuario,
            estado_anterior=estado_anterior,
            estado_nuevo='en_proceso',
            motivo='Solicitud aprobada. Estado actualizado automáticamente a En proceso.',
        )
        return solicitud

    def change_status(
            self, solicitud: Solicitud, nuevo_estado: str,
            motivo: str, usuario
    ) -> Solicitud:

        # RF_37: cambio manual con motivo obligatorio
        # RF_51: si el estado es de cierre, guarda fecha_cierre
        estado_anterior = solicitud.estado
        solicitud.estado = nuevo_estado
        if nuevo_estado in ESTADOS_CIERRE:
            solicitud.fecha_cierre = timezone.now()
        solicitud.save()
        HistorialEstadoSolicitud.objects.create(
            solicitud=solicitud,
            usuario=usuario,
            estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado,
            motivo=motivo,
        )
        return solicitud

    def create_attachment(self, solicitud: Solicitud, archivo, tipo: str, nombre: str,
                      tamanio: int, descripcion: str, usuario) -> Adjunto:
        # RF_38: asocia archivo a la solicitud; fecha_carga se registra sola (auto_now_add)
        anexo = Anexo.objects.create(
            solicitud=solicitud,
            responsable=usuario,
            descripcion=descripcion,
        )
        adjunto = Adjunto.objects.create(
            anexo=anexo,
            archivo=archivo,
            tipo=tipo,
            nombre_archivo=nombre,
            tamanio_bytes=tamanio,
        )
        return adjunto
