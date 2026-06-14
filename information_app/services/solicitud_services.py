from ..repositories.Solicitud_repository import SolicitudRepository

ESTADOS_VALIDOS = {'pendiente', 'en_proceso', 'completada', 'cancelada'}
TIPOS_ADJUNTO_VALIDOS = {'imagen', 'documento', 'video', 'otro'}

TRANSICIONES_PERMITIDAS = {
    'pendiente':   {'en_proceso', 'cancelada'},
    'en_proceso':  {'completada', 'cancelada'},
    'completada':  set(),
    'cancelada':   set(),
}


class SolicitudServices:
    def __init__(self):
        self.repo = SolicitudRepository()

    # ── RF_35: Aprobar solicitud → estado "En proceso" automático ─────────────

    def aprobar_solicitud(self, solicitud_id: int, usuario) -> dict:
        solicitud = self.repo.get_by_id(solicitud_id)
        if not solicitud:
            raise ValueError("Solicitud no encontrada.")
        if solicitud.estado != 'pendiente':
            raise ValueError(
                f"Solo se pueden aprobar solicitudes en estado 'pendiente'. "
                f"Estado actual: '{solicitud.estado}'."
            )
        solicitud = self.repo.aprobar(solicitud, usuario)
        return self._format_solicitud(solicitud)

    # ── RF_34: Consultar horario del laboratorio ───────────────────────────────

    def get_horario_laboratorio(self, laboratorio: str) -> list:
        if not laboratorio or not laboratorio.strip():
            raise ValueError("Debe indicar el nombre del laboratorio.")
        horarios = self.repo.get_horarios_laboratorio(laboratorio.strip())
        if not horarios.exists():
            raise ValueError(f"No se encontraron horarios disponibles para '{laboratorio}'.")
        return [self._format_horario(h) for h in horarios]

    def get_laboratorios_disponibles(self) -> list:
        return list(self.repo.get_laboratorios())

    # ── RF_37: Cambio manual de estado con motivo obligatorio ─────────────────

    def cambiar_estado_manual(self, solicitud_id: int, nuevo_estado: str, motivo: str, usuario) -> dict:
        if not motivo or not motivo.strip():
            raise ValueError("Debe especificar un motivo para el cambio de estado. El campo 'motivo' es obligatorio.")
        if nuevo_estado not in ESTADOS_VALIDOS:
            raise ValueError(
                f"Estado '{nuevo_estado}' no es válido. "
                f"Estados permitidos: {', '.join(sorted(ESTADOS_VALIDOS))}."
            )
        solicitud = self.repo.get_by_id(solicitud_id)
        if not solicitud:
            raise ValueError("Solicitud no encontrada.")
        transiciones = TRANSICIONES_PERMITIDAS.get(solicitud.estado, set())
        if nuevo_estado not in transiciones:
            if not transiciones:
                raise ValueError(f"La solicitud en estado '{solicitud.estado}' no puede ser modificada.")
            raise ValueError(
                f"No es posible cambiar de '{solicitud.estado}' a '{nuevo_estado}'. "
                f"Transiciones permitidas: {', '.join(sorted(transiciones))}."
            )
        solicitud = self.repo.cambiar_estado(solicitud, nuevo_estado, motivo.strip(), usuario)
        return self._format_solicitud(solicitud)

    # ── RF_38: Subir archivos adjuntos ────────────────────────────────────────

    def subir_adjunto(self, solicitud_id: int, archivo, tipo: str, nombre: str,
                      tamanio: int, descripcion: str, usuario) -> dict:
        if not archivo:
            raise ValueError("Debe adjuntar un archivo.")
        if not nombre or not nombre.strip():
            raise ValueError("El campo 'nombre_archivo' es obligatorio.")
        if not descripcion or not descripcion.strip():
            raise ValueError("El campo 'descripcion' es obligatorio.")
        tipo = tipo.strip().lower() if tipo else 'otro'
        if tipo not in TIPOS_ADJUNTO_VALIDOS:
            raise ValueError(
                f"Tipo '{tipo}' no es válido. Tipos permitidos: {', '.join(sorted(TIPOS_ADJUNTO_VALIDOS))}."
            )
        solicitud = self.repo.get_by_id(solicitud_id)
        if not solicitud:
            raise ValueError("Solicitud no encontrada.")
        if solicitud.estado in ('completada', 'cancelada'):
            raise ValueError(f"No se pueden adjuntar archivos a una solicitud en estado '{solicitud.estado}'.")
        adjunto = self.repo.crear_adjunto(
            solicitud=solicitud, archivo=archivo, tipo=tipo,
            nombre=nombre.strip(), tamanio=tamanio,
            descripcion=descripcion.strip(), usuario=usuario,
        )
        return self._format_adjunto(adjunto)

    # ── Formatters ─────────────────────────────────────────────────────────────

    @staticmethod
    def _format_solicitud(solicitud) -> dict:
        return {
            'id':          solicitud.id,
            'estado':      solicitud.estado,
            'prioridad':   solicitud.prioridad,
            'descripcion': solicitud.descripcion,
            'equipo':      solicitud.equipo.nombre,
            'usuario':     solicitud.usuario.nombre,
            'created_at':  solicitud.fecha_creacion.isoformat(),
        }

    @staticmethod
    def _format_horario(horario) -> dict:
        return {
            'id':          horario.id,
            'laboratorio': horario.laboratorio,
            'dia':         horario.get_dia_display(),
            'hora_inicio': str(horario.hora_inicio),
            'hora_fin':    str(horario.hora_fin),
            'disponible':  horario.disponible,
        }

    @staticmethod
    def _format_adjunto(adjunto) -> dict:
        return {
            'adjunto_id':     adjunto.id,
            'nombre_archivo': adjunto.nombre_archivo,
            'tipo':           adjunto.tipo,
            'tamanio_bytes':  adjunto.tamanio_bytes,
            'fecha_carga':    adjunto.fecha_carga.isoformat(),
            'solicitud_id':   adjunto.anexo.solicitud.id,
        }
