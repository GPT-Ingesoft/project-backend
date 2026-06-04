from ..models import Equipo
from django.utils import timezone

class EquipmentRepository:

    # ── Query operations ───────────────────────────────────────────────────────
    def get_by_id(self, equipment_id: int):
        # Returns equipment regardless of status
        return Equipo.objects.filter(id=equipment_id).first()

    def get_all(self):
        # Returns all equipment ordered by name
        return Equipo.objects.all().order_by('nombre')

    # ── Write operations ───────────────────────────────────────────────────────
    def decommission(self, equipment: Equipo, reason: str) -> Equipo:
        equipment.estado = 'dado_de_baja'
        equipment.motivo_baja = reason
        equipment.fecha_baja = timezone.now()
        equipment.save()
        return equipment

    def update_criticality(self, equipment: Equipo, criticality: str) -> Equipo:
        equipment.criticidad = criticality
        equipment.save()
        return equipment