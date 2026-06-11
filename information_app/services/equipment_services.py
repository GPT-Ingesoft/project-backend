from django.db import transaction

from information_app.repositories.equipment_repository import EquipmentRepository

VALID_CRITICALITIES = {'alta', 'media', 'baja'}
REQUIRED_EQUIPMENT_FIELDS = {'name', 'inventory_code', 'model', 'brand', 'serial_number', 'location'}
VALID_STATUSES           = {'operativo', 'en_mantenimiento', 'fuera_de_servicio'}

class EquipmentServices:
    def __init__(self):
        self.equipment_repository = EquipmentRepository()

    # ── Module -> Equipment registration ────────────────────────────────────────────
    @transaction.atomic
    def register_equipment(self, data: dict) -> dict:
        self.validate_equipment_data(data, REQUIRED_EQUIPMENT_FIELDS)

        name           = data['name'].strip()
        inventory_code = data['inventory_code'].strip()
        model          = data['model'].strip()
        brand          = data['brand'].strip()
        serial_number  = data['serial_number'].strip()
        location       = data['location'].strip()
        status         = data.get('status', 'operativo').strip().lower()
        criticality    = data.get('criticality', 'media').strip().lower()

        if status not in VALID_STATUSES:
            raise ValueError(
                f"Status '{status}' is not valid. "
                f"Allowed values: {', '.join(sorted(VALID_STATUSES))}."
            )

        if criticality not in VALID_CRITICALITIES:
            raise ValueError(
                f"Criticality '{criticality}' is not valid. "
                f"Allowed values: {', '.join(sorted(VALID_CRITICALITIES))}."
            )

        if self.equipment_repository.inventory_code_exists(inventory_code):
            raise ValueError(
                f"Inventory code '{inventory_code}' is already registered. "
                "Please use a different code."
            )

        if self.equipment_repository.serial_number_exists(serial_number):
            raise ValueError(
                f"Serial number '{serial_number}' is already registered. "
                "Please verify the serial number."
            )

        equipment = self.equipment_repository.create(
                name=name,
                inventory_code=inventory_code,
                model=model,
                brand=brand,
                serial_number=serial_number,
                location=location,
                status=status,
                criticality=criticality,
            )

        return self.format_equipment_data(equipment)

    @staticmethod
    def validate_equipment_data(data: dict, fields: list) -> None:
        for field in fields:
            value = data.get(field)
            if value is None or str(value).strip() == '':
                raise ValueError(f"Field '{field}' is required and cannot be empty.")

    # ── Module -> Equipment management ────────────────────────────────────────────────
    @staticmethod
    def format_equipment_data(equipment) -> dict:
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
