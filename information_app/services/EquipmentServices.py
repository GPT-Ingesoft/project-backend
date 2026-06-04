from ..repositories.EquipmentRepository import EquipmentRepository

# Criticality values match the DB definitions in models.py (kept in Spanish)
VALID_CRITICALITIES = {'alta', 'media', 'baja'}

class EquipmentServices:
    def __init__(self):
        self.equipment_repository = EquipmentRepository()

    # ── Module -> Equipment management ────────────────────────────────────────────────
    @staticmethod
    def format_equipment_data(equipment) -> dict:
        # Maps Spanish model field names to English response keys
        return {
            'id':               equipment.id,
            'name':             equipment.nombre,
            'inventory_code':   equipment.codigo_inventario,
            'model':            equipment.modelo,
            'brand':            equipment.marca,
            'serial_number':    equipment.numero_serie,
            'location':         equipment.ubicacion,
            'status':           equipment.estado,
            'criticality':      equipment.criticidad,
            'decommission_reason': equipment.motivo_baja,
            'decommission_date':   equipment.fecha_baja.isoformat() if equipment.fecha_baja else None,
            'created_at':       equipment.fecha_creacion.isoformat(),
        }

    def list_equipment(self) -> list:
        equipment = self.equipment_repository.get_all()
        return [self.format_equipment_data(e) for e in equipment]

    def decommission_equipment(self, equipment_id: int, reason: str) -> dict:
        equipment = self.equipment_repository.get_by_id(equipment_id)
        if not equipment:
            raise ValueError("Equipment not found.")

        if equipment.estado == 'dado_de_baja':
            raise ValueError(f"Equipment '{equipment.nombre}' is already decommissioned.")

        equipment = self.equipment_repository.decommission(equipment, reason)
        return self.format_equipment_data(equipment)

    def update_criticality(self, equipment_id: int, criticality: str) -> dict:
        if criticality not in VALID_CRITICALITIES:
            raise ValueError(f"Criticality '{criticality}' is not valid. Allowed values: {', '.join(VALID_CRITICALITIES)}.")

        equipment = self.equipment_repository.get_by_id(equipment_id)
        if not equipment:
            raise ValueError("Equipment not found.")

        if equipment.estado == 'dado_de_baja':
            raise ValueError(f"Equipment '{equipment.nombre}' is decommissioned and cannot be modified.")

        equipment = self.equipment_repository.update_criticality(equipment, criticality)
        return self.format_equipment_data(equipment)

    def verify_availability(self, equipment_id: int) -> dict:
        equipment = self.equipment_repository.get_by_id(equipment_id)
        if not equipment:
            raise ValueError("Equipment not found.")

        if equipment.estado == 'dado_de_baja':
            raise ValueError(
                f"Equipment '{equipment.nombre}' is decommissioned and cannot be used "
                f"or assigned to maintenance. Reason: {equipment.motivo_baja}"
            )

        return self.format_equipment_data(equipment)