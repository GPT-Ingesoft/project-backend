from dataclasses import dataclass
from django.utils import timezone
from information_app.models import (
    Asignacion, Solicitud, Tecnico,
    HistorialEstadoSolicitud, Anexo, Adjunto, HorarioAtencion
)
from information_app.repositories.repository_utils import BaseRepository


ESTADOS_CIERRE = {'completada', 'cancelada'}

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

    # ── Escritura ─────────────────────────────────────────────────────────

    def link_equipment(self, solicitud_id: int, equipment_id: int):
        sol = self.get_by_id(solicitud_id)
        if not sol:
            raise ValueError("Solicitud no encontrada.")
        if sol.equipo:
            raise ValueError("Ya tiene equipo registrado.")

        sol.equipo_id = equipment_id
        sol.datos_equipo_solicitado = None
        sol.save()

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

@dataclass
class AttachmentData:
    archivo: object
    tipo: str
    nombre: str
    tamanio: int
    descripcion: str
