from ..repositories.EquipoRepository import EquipoRepository

CRITICIDADES_VALIDAS = {'alta', 'media', 'baja'}

class EquipoServices:
    def __init__(self):
        self.equipo_repository = EquipoRepository()

    @staticmethod
    def formato_datos_equipo(equipo) -> dict:
        return {
            'id':                 equipo.id,
            'nombre':             equipo.nombre,
            'codigo_inventario':  equipo.codigo_inventario,
            'modelo':             equipo.modelo,
            'marca':              equipo.marca,
            'numero_serie':       equipo.numero_serie,
            'ubicacion':          equipo.ubicacion,
            'estado':             equipo.estado,
            'criticidad':         equipo.criticidad,
            'motivo_baja':        equipo.motivo_baja,
            'fecha_baja':         equipo.fecha_baja.isoformat() if equipo.fecha_baja else None,
            'fecha_creacion':     equipo.fecha_creacion.isoformat(),
        }

    def listar_equipos(self) -> list:
        equipos = self.equipo_repository.listar_todos()
        return [self.formato_datos_equipo(e) for e in equipos]

    def dar_de_baja(self, equipo_id: int, motivo: str) -> dict:
        equipo = self.equipo_repository.obtener_por_id(equipo_id)
        if not equipo:
            raise ValueError("Equipo no encontrado.")

        if equipo.estado == 'dado_de_baja':
            raise ValueError(f"El equipo '{equipo.nombre}' ya se encuentra dado de baja.")

        equipo = self.equipo_repository.dar_de_baja(equipo, motivo)
        return self.formato_datos_equipo(equipo)

    def cambiar_criticidad(self, equipo_id: int, criticidad: str) -> dict:
        if criticidad not in CRITICIDADES_VALIDAS:
            raise ValueError(f"Criticidad '{criticidad}' no válida. Valores permitidos: {', '.join(CRITICIDADES_VALIDAS)}.")

        equipo = self.equipo_repository.obtener_por_id(equipo_id)
        if not equipo:
            raise ValueError("Equipo no encontrado.")

        if equipo.estado == 'dado_de_baja':
            raise ValueError(f"El equipo '{equipo.nombre}' está dado de baja y no puede ser modificado.")

        equipo = self.equipo_repository.actualizar_criticidad(equipo, criticidad)
        return self.formato_datos_equipo(equipo)

    def verificar_disponibilidad(self, equipo_id: int) -> dict:
        equipo = self.equipo_repository.obtener_por_id(equipo_id)
        if not equipo:
            raise ValueError("Equipo no encontrado.")

        if equipo.estado == 'dado_de_baja':
            raise ValueError(f"El equipo '{equipo.nombre}' está dado de baja y no puede ser utilizado ni asignado a mantenimiento. Motivo: {equipo.motivo_baja}")

        return self.formato_datos_equipo(equipo)