from django.db import transaction
from information_app.repositories.request_repository import (
    RequestRepository,
    AttachmentData,
)
from information_app.services.services_utils import (
    format_technician_data,
    validate_enum,
)

ESTADOS_VALIDOS         = {'pendiente', 'en_proceso', 'completada', 'cancelada'}
TIPOS_ADJUNTO_VALIDOS   = {'imagen', 'documento', 'video', 'otro'}
REASSIGNABLE_STATUSES   = {'pendiente', 'en_proceso'}
TRANSICIONES_PERMITIDAS = {
    'pendiente':   {'en_proceso', 'cancelada'},
    'en_proceso':  {'completada', 'cancelada'},
    'completada':  set(),
    'cancelada':   set(),
}

class RequestServices:
    def __init__(self):
        self.request_repository = RequestRepository()

    # ── request ────────────────────────────────────────────
    @transaction.atomic
    def create_request(self, data: dict, usuario) -> dict:
        if not data.get('datos_equipo'):
            raise ValueError("Debe proporcionar 'datos_equipo'.")

        sol = self.request_repository.create(
            descripcion=data['descripcion'],
            prioridad=data.get('prioridad', 'media'),
            usuario=usuario,
            datos_equipo_solicitado=data['datos_equipo'],
            equipo_id=None
        )
        return self._format_request(sol)

    def get_request_details(self, solicitud_id: int) -> dict:
        sol = self.get_request_or_fail(solicitud_id)
        return {
            **self._format_request(sol),
            'datos_equipo_solicitado': sol.datos_equipo_solicitado
        }

    def link_equipment(self, solicitud_id: int, equipment_id: int):
        return self.request_repository.link_equipment(solicitud_id, equipment_id)

    # ── Reasignación de técnicos ────────────────────────────────────────────

    @transaction.atomic
    def reassign_technicians(self, request_id: int, data: dict) -> dict:
        technician_ids = self._validate_technician_ids(data)
        request = self.get_request_or_fail(request_id)

        if request.estado not in REASSIGNABLE_STATUSES:
            raise ValueError(
                "Technicians can only be reassigned when the request status is "
                "'pendiente' or 'en_proceso'."
            )

        technicians = self.request_repository.get_technicians_by_ids(technician_ids)
        found_ids = {t.usuario.id for t in technicians}
        missing_ids = sorted(set(technician_ids) - found_ids)
        if missing_ids:
            raise ValueError(f"Technician users not found: {', '.join(map(str, missing_ids))}.")

        self.request_repository.replace_assigned_technicians(request, technicians)
        return self._format_assignment(request, technicians)

    # ── Aprobación ──────────────────────────────────────────────────────────

    @transaction.atomic
    def approve_request(self, solicitud_id: int, usuario) -> dict:
        solicitud = self.get_request_or_fail(solicitud_id)
        if solicitud.estado != 'pendiente':
            raise ValueError(
                f"Solo se pueden aprobar solicitudes en estado 'pendiente'. "
                f"Estado actual: '{solicitud.estado}'."
            )
        solicitud = self.request_repository.approve(solicitud, usuario)
        return self._format_request(solicitud)

    # ── Horarios ─────────────────────────────────────────────────────────────

    def get_lab_schedule(self, laboratorio: str) -> list:
        if not laboratorio or not laboratorio.strip():
            raise ValueError("Debe indicar el nombre del laboratorio.")
        horarios = self.request_repository.get_lab_schedules(laboratorio.strip())
        if not horarios.exists():
            raise ValueError(f"No se encontraron horarios disponibles para '{laboratorio}'.")
        return [self._format_schedule(h) for h in horarios]

    def get_available_laboratories(self) -> list:
        return list(self.request_repository.get_laboratories())

    # ── Cambio de estado ────────────────────────────────────────────────────

    @transaction.atomic
    def change_status_manually(self, solicitud_id: int, data: dict, usuario) -> dict:
        nuevo_estado = validate_enum(data.get('estado', '').strip(), ESTADOS_VALIDOS, 'Estado')
        motivo = data.get('motivo', '').strip()
        if not motivo:
            raise ValueError("Debe especificar un motivo para el cambio de estado.")

        solicitud = self.get_request_or_fail(solicitud_id)
        transiciones = TRANSICIONES_PERMITIDAS.get(solicitud.estado, set())
        if nuevo_estado not in transiciones:
            if not transiciones:
                raise ValueError(
                    f"La solicitud en estado '{solicitud.estado}' no puede ser modificada."
                )

            raise ValueError(
                f"No es posible cambiar de '{solicitud.estado}' a '{nuevo_estado}'. "
                f"Transiciones permitidas: {', '.join(sorted(transiciones))}."
            )

        solicitud = self.request_repository.change_status(solicitud, nuevo_estado, motivo, usuario)
        return self._format_request(solicitud)

    # ── Adjuntos ─────────────────────────────────────────────────────────────

    @transaction.atomic
    def upload_attachment(self, solicitud_id: int, data: dict, usuario) -> dict:
        archivo = data.get('archivo')
        if not archivo:
            raise ValueError("Debe adjuntar un archivo.")

        nombre      = data.get('nombre', '').strip()
        descripcion = data.get('descripcion', '').strip()

        if not nombre:
            raise ValueError("El campo 'nombre_archivo' es obligatorio.")
        if not descripcion:
            raise ValueError("El campo 'descripcion' es obligatorio.")

        tipo = validate_enum(
            data.get('tipo', 'otro').strip().lower(),
            TIPOS_ADJUNTO_VALIDOS,
            'Tipo'
        )

        tamanio = data.get('tamanio', 0)

        solicitud = self.get_request_or_fail(solicitud_id)
        if solicitud.estado in ('completada', 'cancelada'):
            raise ValueError(
                f"No se pueden adjuntar archivos a una solicitud en estado "
                f"'{solicitud.estado}'."
            )

        adjunto = self.request_repository.create_attachment(
            solicitud=solicitud,
            attachment=AttachmentData(
                archivo=archivo,
                tipo=tipo,
                nombre=nombre,
                tamanio=tamanio,
                descripcion=descripcion,
            ),
            usuario=usuario,
        )
        return self._format_attachment(adjunto)

    # ── Formatters ───────────────────────────────────────────────────────────

    @staticmethod
    def _format_request(sol) -> dict:
        return {
            'id': sol.id, 'estado': sol.estado, 'prioridad': sol.prioridad,
            'descripcion': sol.descripcion,
            'equipo': sol.equipo.nombre if sol.equipo else None,
            'usuario': sol.usuario.nombre, 'created_at': sol.fecha_creacion.isoformat(),
        }

    @staticmethod
    def _format_schedule(horario) -> dict:
        return {
            'id':          horario.id,
            'laboratorio': horario.laboratorio,
            'dia':         horario.get_dia_display(),
            'hora_inicio': str(horario.hora_inicio),
            'hora_fin':    str(horario.hora_fin),
            'disponible':  horario.disponible,
        }

    @staticmethod
    def _format_attachment(adjunto) -> dict:
        return {
            'adjunto_id':     adjunto.id,
            'nombre_archivo': adjunto.nombre_archivo,
            'tipo':           adjunto.tipo,
            'tamanio_bytes':  adjunto.tamanio_bytes,
            'fecha_carga':    adjunto.fecha_carga.isoformat(),
            'solicitud_id':   adjunto.anexo.solicitud.id,
        }

    @staticmethod
    def _format_assignment(request, technicians) -> dict:
        return {
            'request': {
                'id': request.id,
                'status': request.estado,
                'description': request.descripcion,
            },
            'assigned_technicians': [
                format_technician_data(t) for t in technicians
            ],
        }

    # ── Helpers ──────────────────────────────────────────────────────────────

    def get_request_or_fail(self, request_id: int):
        request = self.request_repository.get_by_id(request_id)
        if not request:
            raise ValueError("Request not found.")
        return request

    @staticmethod
    def _validate_technician_ids(data: dict) -> list:
        technician_ids = data.get('technician_ids')
        if not isinstance(technician_ids, list) or not technician_ids:
            raise ValueError("Field 'technician_ids' is required and must be a non-empty list.")
        if not all(isinstance(tid, int) for tid in technician_ids):
            raise ValueError("Field 'technician_ids' must contain only integer values.")
        unique_ids = list(dict.fromkeys(technician_ids))
        if len(unique_ids) != len(technician_ids):
            raise ValueError("Field 'technician_ids' cannot contain duplicated values.")
        return unique_ids
