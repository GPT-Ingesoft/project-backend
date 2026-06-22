from pathlib import Path

from django.db import transaction
from information_app.repositories.request_repository import (
    RequestRepository,
    AttachmentData,
)
from information_app.services.services_utils import (
    format_technician_data,
    validate_enum,
)
from information_app.services.notification_services import NotificationServices

ESTADOS_VALIDOS         = {'pendiente', 'en_proceso', 'completada', 'cancelada'}
PRIORIDADES_VALIDAS     = {'baja', 'media', 'alta'}
TIPOS_ADJUNTO_VALIDOS   = {'imagen', 'documento', 'video', 'otro'}
FORMATOS_ADJUNTO_POR_TIPO = {
    'imagen': {'.jpeg', '.jpg', '.png', '.webp'},
    'documento': {'.csv', '.doc', '.docx', '.pdf', '.txt', '.xls', '.xlsx'},
    'video': {'.mov', '.mp4', '.webm'},
    'otro': {'.zip'},
}
TAMANIO_MAXIMO_ADJUNTO_BYTES = 10 * 1024 * 1024
REASSIGNABLE_STATUSES   = {'pendiente', 'en_proceso'}
SERVER_MANAGED_FIELDS   = {'estado', 'fecha_creacion', 'fecha_cierre', 'usuario_id'}
TRANSICIONES_PERMITIDAS = {
    'pendiente':   {'en_proceso', 'cancelada'},
    'en_proceso':  {'completada', 'cancelada'},
    'completada':  set(),
    'cancelada':   set(),
}

class RequestServices:
    def __init__(self):
        self.request_repository = RequestRepository()
        self.notification_service = NotificationServices()

    @transaction.atomic
    def create_request(self, data: dict, usuario) -> dict:
        forbidden = sorted(SERVER_MANAGED_FIELDS.intersection(data))
        if forbidden:
            raise ValueError(
                "Los campos administrados por el servidor no pueden enviarse: "
                f"{', '.join(forbidden)}."
            )

        descripcion = str(data.get('descripcion', '')).strip()
        if not descripcion:
            raise ValueError("El campo 'descripcion' es obligatorio.")

        equipment_id = data.get('equipo_id')
        if not isinstance(equipment_id, int) or isinstance(equipment_id, bool):
            raise ValueError("El campo 'equipo_id' es obligatorio y debe ser un entero.")

        prioridad = validate_enum(
            str(data.get('prioridad', 'media')).strip().lower(),
            PRIORIDADES_VALIDAS,
            'Prioridad',
        )
        equipo = self.request_repository.get_equipment_by_id(equipment_id)
        if not equipo:
            raise ValueError("Equipo no encontrado.")
        if equipo.estado == 'dado_de_baja':
            raise ValueError("No se pueden crear solicitudes para un equipo dado de baja.")

        horario = self._get_valid_schedule(data.get('horario_id'), equipo)
        solicitud = self.request_repository.create_request(
            descripcion=descripcion,
            prioridad=prioridad,
            usuario=usuario,
            equipo=equipo,
            horario_agendado=horario,
        )
        return self._format_request(solicitud)

    def get_request(self, solicitud_id: int, usuario) -> dict:
        solicitud = self._get_request_or_fail(solicitud_id)
        allowed = (
            usuario.rol == 'laboratorista'
            or solicitud.usuario_id == usuario.id
            or self.request_repository.is_user_assigned(solicitud, usuario.id)
        )
        if not allowed:
            raise PermissionError("No tiene permisos para consultar esta solicitud.")
        return self._format_request(solicitud)

    # ── Reasignación de técnicos ────────────────────────────────────────────

    @transaction.atomic
    def reassign_technicians(self, request_id: int, data: dict) -> dict:
        technician_ids = self._validate_technician_ids(data)
        request = self._get_request_or_fail(request_id)

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

        available_ids = {
            technician.usuario.id
            for technician in self.request_repository.get_available_technicians(request)
        }
        unavailable_ids = sorted(set(technician_ids) - available_ids)
        if unavailable_ids:
            raise ValueError(
                f"Technicians are not available: {', '.join(map(str, unavailable_ids))}."
            )

        self.request_repository.replace_assigned_technicians(request, technicians)
        return self._format_assignment(request, technicians)

    def get_available_technicians(self, solicitud_id: int) -> list:
        solicitud = self._get_request_or_fail(solicitud_id)
        return [
            format_technician_data(technician)
            for technician in self.request_repository.get_available_technicians(solicitud)
        ]

    # ── Aprobación ──────────────────────────────────────────────────────────

    @transaction.atomic
    def approve_request(self, solicitud_id: int, usuario) -> dict:
        solicitud = self._get_request_or_fail(solicitud_id)
        if solicitud.estado != 'pendiente':
            raise ValueError(
                f"Solo se pueden aprobar solicitudes en estado 'pendiente'. "
                f"Estado actual: '{solicitud.estado}'."
            )
        estado_anterior = solicitud.estado
        solicitud = self.request_repository.approve(solicitud, usuario)
        self.notification_service.notify_request_status_change(
            solicitud,
            estado_anterior,
        )
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

        solicitud = self._get_request_or_fail(solicitud_id)
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

        estado_anterior = solicitud.estado
        solicitud = self.request_repository.change_status(solicitud, nuevo_estado, motivo, usuario)
        self.notification_service.notify_request_status_change(
            solicitud,
            estado_anterior,
            motivo,
        )
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

        tamanio = getattr(archivo, 'size', data.get('tamanio', 0))
        self._validate_attachment_size(tamanio)
        tipo = self._validate_attachment_format(archivo, data.get('tipo'))

        solicitud = self._get_request_or_fail(solicitud_id)
        if solicitud.estado in ('completada', 'cancelada'):
            raise ValueError(
                f"No se pueden adjuntar archivos a una solicitud en estado "
                f"'{solicitud.estado}'."
            )
        if usuario and not self.request_repository.is_user_assigned(solicitud, usuario.id):
            raise PermissionError(
                "Solo un técnico asignado a la solicitud puede adjuntar evidencias."
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

    @staticmethod
    def _validate_attachment_size(tamanio) -> None:
        if not isinstance(tamanio, int) or isinstance(tamanio, bool) or tamanio <= 0:
            raise ValueError("El archivo adjunto debe contener información.")
        if tamanio > TAMANIO_MAXIMO_ADJUNTO_BYTES:
            maximo_mb = TAMANIO_MAXIMO_ADJUNTO_BYTES // (1024 * 1024)
            raise ValueError(
                f"El archivo supera el tamaño máximo permitido de {maximo_mb} MB."
            )

    @staticmethod
    def _validate_attachment_format(archivo, requested_type) -> str:
        extension = Path(getattr(archivo, 'name', '')).suffix.lower()
        inferred_type = next(
            (
                attachment_type
                for attachment_type, extensions in FORMATOS_ADJUNTO_POR_TIPO.items()
                if extension in extensions
            ),
            None,
        )
        if not inferred_type:
            allowed = sorted(
                file_extension
                for extensions in FORMATOS_ADJUNTO_POR_TIPO.values()
                for file_extension in extensions
            )
            raise ValueError(
                "El formato del archivo no está permitido. "
                f"Formatos admitidos: {', '.join(allowed)}."
            )

        if requested_type is None or not str(requested_type).strip():
            return inferred_type

        attachment_type = validate_enum(
            str(requested_type).strip().lower(),
            TIPOS_ADJUNTO_VALIDOS,
            'Tipo',
        )
        if attachment_type != inferred_type:
            raise ValueError(
                f"El archivo '{archivo.name}' no corresponde al tipo "
                f"'{attachment_type}'."
            )
        return attachment_type

    # ── Formatters ───────────────────────────────────────────────────────────

    @staticmethod
    def _format_request(solicitud) -> dict:
        return {
            'id':          solicitud.id,
            'estado':      solicitud.estado,
            'prioridad':   solicitud.prioridad,
            'descripcion': solicitud.descripcion,
            'equipo':      solicitud.equipo.nombre,
            'usuario':     solicitud.usuario.nombre,
            'created_at':  solicitud.fecha_creacion.isoformat(),
            'horario_agendado': (
                RequestServices._format_schedule(solicitud.horario_agendado)
                if solicitud.horario_agendado else None
            ),
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

    def _get_request_or_fail(self, request_id: int):
        request = self.request_repository.get_by_id(request_id)
        if not request:
            raise ValueError("Request not found.")
        return request

    def _get_valid_schedule(self, schedule_id, equipment):
        if schedule_id is None:
            return None
        if not isinstance(schedule_id, int) or isinstance(schedule_id, bool):
            raise ValueError("El campo 'horario_id' debe ser un entero.")

        schedule = self.request_repository.get_schedule_by_id(schedule_id)
        if not schedule:
            raise ValueError("Horario de atención no encontrado.")
        if not schedule.disponible:
            raise ValueError("El horario de atención seleccionado no está disponible.")
        if schedule.hora_inicio >= schedule.hora_fin:
            raise ValueError("El horario de atención tiene un rango de horas inválido.")
        if schedule.laboratorio.strip().casefold() != equipment.ubicacion.strip().casefold():
            raise ValueError(
                "El horario de atención no corresponde a la ubicación del equipo."
            )
        return schedule

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
