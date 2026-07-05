from dataclasses import dataclass
from django.utils import timezone
from information_app.models import (
    Asignacion, Equipo, Solicitud, Tecnico,
    HistorialEstadoSolicitud, Anexo, Adjunto, HorarioAtencion, Intervencion
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

    def delete_instance(self, instance):
        raise PermissionError(
            "Las solicitudes de mantenimiento no pueden eliminarse ni ocultarse "
            "del sistema."
        )

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

    def list_for_user(self, usuario):
        qs = (
            Solicitud.objects
            .select_related('usuario', 'equipo', 'horario_agendado')
            .prefetch_related('asignaciones__tecnico__usuario')
        )
        if usuario.rol == 'laboratorista':
            return qs.order_by('-fecha_creacion')
        if usuario.rol == 'tecnico':
            return (
                qs.filter(asignaciones__tecnico__usuario_id=usuario.id, asignaciones__activa=True)
                .distinct()
                .order_by('-fecha_creacion')
            )
        return qs.filter(usuario_id=usuario.id).order_by('-fecha_creacion')

    def get_full_request_by_id(self, solicitud_id: int):
        return (
            Solicitud.objects
            .select_related('usuario', 'equipo', 'horario_agendado')
            .prefetch_related(
                'asignaciones__tecnico__usuario',
                'historial_estados__usuario',
                'anexos__responsable',
                'anexos__adjuntos',
                'intervenciones__tecnico__usuario',
            )
            .filter(id=solicitud_id)
            .first()
        )

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

    def get_technician_by_user_id(self, user_id: int):
        return Tecnico.objects.select_related('usuario').filter(usuario_id=user_id).first()

    def get_attachments(self, solicitud: Solicitud):
        return (
            Adjunto.objects
            .select_related('anexo', 'anexo__responsable')
            .filter(anexo__solicitud=solicitud)
            .order_by('-fecha_carga')
        )

    def get_attachment_by_id(self, attachment_id: int):
        return (
            Adjunto.objects
            .select_related('anexo', 'anexo__solicitud')
            .filter(id=attachment_id)
            .first()
        )

    def get_interventions(self, solicitud: Solicitud):
        return (
            Intervencion.objects
            .select_related('tecnico__usuario')
            .filter(solicitud=solicitud)
            .order_by('-fecha_intervencion')
        )

    # ── Escritura ─────────────────────────────────────────────────────────

    def create_request(  # pylint: disable=too-many-arguments
        self,
        *,
        descripcion: str,
        prioridad: str,
        usuario,
        equipo=None,
        horario_agendado=None,
        datos_equipo_solicitado=None,
    ) -> Solicitud:
        return Solicitud.objects.create(
            descripcion=descripcion,
            prioridad=prioridad,
            estado='pendiente',
            usuario=usuario,
            equipo=equipo,
            horario_agendado=horario_agendado,
            datos_equipo_solicitado=datos_equipo_solicitado,
        )

    def link_equipment(self, solicitud_id: int, equipment):
        sol = self.get_by_id(solicitud_id)
        if not sol:
            raise ValueError("Solicitud no encontrada.")
        if sol.equipo:
            raise ValueError("Ya tiene equipo registrado.")

        sol.equipo = equipment
        sol.datos_equipo_solicitado = None
        sol.save(update_fields=['equipo', 'datos_equipo_solicitado'])
        return sol

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

    def create_intervention(
        self, solicitud: Solicitud, tecnico: Tecnico, descripcion: str, observaciones: str
    ) -> Intervencion:
        return Intervencion.objects.create(
            solicitud=solicitud,
            tecnico=tecnico,
            descripcion=descripcion,
            observaciones=observaciones,
        )
