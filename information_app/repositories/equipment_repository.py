from django.utils import timezone
from information_app.models import Equipo, Intervencion
from information_app.repositories.repository_utils import BaseRepository

class EquipmentRepository(BaseRepository):
    def get_model(self):
        return Equipo

    # ── Query operations ──────────────────────────────────────────

    def get_all(self):
        return super().get_all(order_by='nombre')

    def inventory_code_exists(self, inventory_code: str) -> bool:
        return self.exists(codigo_inventario=inventory_code)

    def serial_number_exists(self, serial_number: str) -> bool:
        return self.exists(numero_serie=serial_number)

    def inventory_code_exists_for_other(self, inventory_code: str, equipment_id: int) -> bool:
        return self.exists_excluding(equipment_id, codigo_inventario=inventory_code)

    def get_equipment_with_history(self, equipment_id: int):
        return (
            self.get_model()
            .prefetch_related(
                'solicitudes',
                'solicitudes__intervenciones',
                'solicitudes__intervenciones__tecnico',
                'solicitudes__intervenciones__tecnico__usuario',
                'solicitudes__asignaciones',
                'solicitudes__asignaciones__tecnico',
                'solicitudes__asignaciones__tecnico__usuario',
                'solicitudes__historial_estados',
            )
            .filter(id=equipment_id)
            .first()
        )

    # ── Write operations ─────────────────────────────────────────────────────────

    def decommission(self, equipment: Equipo, reason: str) -> Equipo:
        equipment.estado = 'dado_de_baja'
        equipment.motivo_baja = reason
        equipment.fecha_baja = timezone.now()
        equipment.save()
        return equipment

    def create_intervention(
        self, solicitud, tecnico, descripcion: str, observaciones: str = None
    ) -> Intervencion:
        return Intervencion.objects.create(
            solicitud=solicitud,
            tecnico=tecnico,
            descripcion=descripcion,
            observaciones=observaciones,
        )
