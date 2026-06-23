from dataclasses import dataclass
from django.utils import timezone
from information_app.models import (
    Asignacion, Equipo, Solicitud, Tecnico,
    HistorialEstadoSolicitud, Anexo, Adjunto, HorarioAtencion
)
from information_app.repositories.repository_utils import BaseRepository


ESTADOS_CIERRE = {'completada', 'cancelada'}

@dataclass
class AttachmentData:
    archivo: object
    tipo: str
    nombre: str
    tamanio: int
    descripcion: str

class RequestRepository(BaseRepository):

    def get_model(self):
        return Solicitud

    # ── Query operations ─────────────────────────────────────────────────────────

    def get_technicians_by_ids(self, technician_ids):
        return list(
            Tecnico.objects
            .select_related('usuario')
            .filter(usuario_id__in=technician_ids)
        )

    def get_available_technicians(self, solicitud: Solicitud):
        technicians = Tecnico.objects.select_related('usuario').filter(usuario__activo=True)
        if not solicitud.horario_agendado_id:
            return technicians.order_by('usuario__nombre')

        occupied_ids = (
            Asignacion.objects
            .filter(
                activa=True,
                solicitud__estado__in=('pendiente', 'en_proceso'),
                solicitud__horario_agendado_id=solicitud.horario_agendado_id,
            )
            .exclude(solicitud=solicitud)
            .values_list('tecnico_id', flat=True)
        )
        return technicians.exclude(usuario_id__in=occupied_ids).order_by('usuario__nombre')

    def get_lab_schedules(self, laboratorio: str):
        return (
            HorarioAtencion.objects
            .filter(laboratorio=laboratorio, disponible=True)
            .order_by('dia', 'hora_inicio')
        )

    def get_laboratories(self):
        return (
            HorarioAtencion.objects
            .values_list('laboratorio', flat=True)
            .distinct()
            .order_by('laboratorio')
        )

    def get_schedule_by_id(self, schedule_id: int):
        return HorarioAtencion.objects.filter(id=schedule_id).first()

    def get_equipment_by_id(self, equipment_id: int):
        return Equipo.objects.filter(id=equipment_id).first()

    @staticmethod
    def is_user_assigned(solicitud: Solicitud, user_id: int) -> bool:
        return Asignacion.objects.filter(
            solicitud=solicitud,
            tecnico__usuario_id=user_id,
            activa=True,
        ).exists()

    @staticmethod
    def get_active_technician_ids(solicitud: Solicitud) -> set:
        return set(
            Asignacion.objects.filter(solicitud=solicitud, activa=True)
            .values_list('tecnico_id', flat=True)
        )

    # ── Escritura ─────────────────────────────────────────────────────────

    def create_request(  # pylint: disable=too-many-arguments
        self,
        *,
        descripcion: str,
        prioridad: str,
        usuario,
        equipo,
        horario_agendado=None,
    ) -> Solicitud:
        return Solicitud.objects.create(
            descripcion=descripcion,
            prioridad=prioridad,
            estado='pendiente',
            usuario=usuario,
            equipo=equipo,
            horario_agendado=horario_agendado,
        )

    def replace_assigned_technicians(self, request: Solicitud, technicians):
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

    def approve(self, solicitud: Solicitud, usuario) -> Solicitud:
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
        self, solicitud: Solicitud, nuevo_estado: str, motivo: str, usuario
    ) -> Solicitud:
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

    def create_attachment(
        self, solicitud: Solicitud, attachment: AttachmentData, usuario
    ) -> Adjunto:
        anexo = Anexo.objects.create(
            solicitud=solicitud,
            responsable=usuario,
            descripcion=attachment.descripcion,
        )
        return Adjunto.objects.create(
            anexo=anexo,
            archivo=attachment.archivo,
            tipo=attachment.tipo,
            nombre_archivo=attachment.nombre,
            tamanio_bytes=attachment.tamanio,
        )
