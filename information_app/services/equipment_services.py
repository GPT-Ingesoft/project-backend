from django.db import transaction

from information_app.repositories.equipment_repository import EquipmentRepository
from information_app.services.services_utils import (
    format_technician_data,
    validate_required_fields,
    validate_enum
)

VALID_CRITICALITIES = {'alta', 'media', 'baja'}
REQUIRED_EQUIPMENT_FIELDS = {
    'name', 'inventory_code', 'model',
    'brand', 'serial_number', 'location'
}
VALID_STATUSES           = {'operativo', 'en_mantenimiento', 'fuera_de_servicio'}

class EquipmentServices:
    def __init__(self):
        self.equipment_repository = EquipmentRepository()

    # ── Module -> Equipment registration ────────────────────────────────────────────
    @transaction.atomic
    def register_equipment(self, data: dict) -> dict:
        validate_required_fields(data, REQUIRED_EQUIPMENT_FIELDS)

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

    @transaction.atomic
    def update_equipment(self, equipment_id: int, data: dict) -> dict:

        if 'serial_number' in data:
            raise ValueError("Field 'serial_number' cannot be modified.")

        equipment = self.equipment_repository.get_by_id(equipment_id)
        if not equipment:
            raise ValueError("Equipment not found.")

        if equipment.estado == 'dado_de_baja':
            raise ValueError(
                f"Equipment '{equipment.nombre}' is decommissioned and cannot be modified."
            )

        fields_to_update = {}

        for field_key, db_field in [
            ('name', 'nombre'),
            ('inventory_code', 'codigo_inventario'),
            ('model', 'modelo'),
            ('brand', 'marca'),
            ('location', 'ubicacion'),
        ]:
            if field_key in data:
                _, value = self._validate_and_transform_field(data, field_key, db_field)
                if field_key == 'inventory_code':
                    if self.equipment_repository.inventory_code_exists_for_other(
                        value, equipment_id
                    ):
                        raise ValueError(
                            f"Inventory code '{value}' is already registered. "
                            "Please use a different code."
                        )
                fields_to_update[db_field] = value

        if 'status' in data:
            st = str(data['status']).strip().lower()
            fields_to_update['estado'] = validate_enum(st, VALID_STATUSES, 'Status')

        if 'criticality' in data:
            crit = str(data['criticality']).strip().lower()
            fields_to_update['criticidad'] = validate_enum(
                crit, VALID_CRITICALITIES, 'Criticality'
            )

        if not fields_to_update:
            raise ValueError("No valid fields provided for update.")

        equipment = self.equipment_repository.update(equipment, fields_to_update)
        return self.format_equipment_data(equipment)

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

            'decommission_date':   (
                equipment.fecha_baja.isoformat() if equipment.fecha_baja else None,
            ),

            'created_at':       equipment.fecha_creacion.isoformat(),
        }

    @staticmethod
    def format_status_history_data(status_history) -> dict:
        return {
            'id': status_history.id,
            'previous_status': status_history.estado_anterior,
            'new_status': status_history.estado_nuevo,
            'reason': status_history.motivo,
            'changed_at': status_history.fecha_cambio.isoformat(),
            'changed_by': {
                'id': status_history.usuario.id,
                'name': status_history.usuario.nombre,
                'email': status_history.usuario.correo,
            } if status_history.usuario else None,
        }

    @staticmethod
    def format_intervention_data(intervention) -> dict:
        return {
            'id': intervention.id,
            'description': intervention.descripcion,
            'observations': intervention.observaciones,
            'performed_at': intervention.fecha_intervencion.isoformat(),
            'technician': format_technician_data(
                intervention.tecnico
            ),
        }

    @staticmethod
    def format_request_history_data(request) -> dict:
        return {
            'id': request.id,
            'description': request.descripcion,
            'priority': request.prioridad,
            'status': request.estado,
            'created_at': request.fecha_creacion.isoformat(),
            'scheduled_attention': {
                'id': request.horario_agendado.id,
                'laboratory': request.horario_agendado.laboratorio,
                'day': request.horario_agendado.dia,
                'start_time': request.horario_agendado.hora_inicio.isoformat(),
                'end_time': request.horario_agendado.hora_fin.isoformat(),
            } if request.horario_agendado else None,
            'assigned_technicians': [
                format_technician_data(
                    assignment.tecnico
                )
                for assignment in request.asignaciones.all()
            ],
            'status_history': [
                EquipmentServices.format_status_history_data(status_change)
                for status_change in request.historial_estados.all()
            ],
            'interventions': [
                EquipmentServices.format_intervention_data(intervention)
                for intervention in request.intervenciones.all()
            ],
        }

    def get_equipment_history(self, equipment_id: int) -> dict:
        equipment = self.equipment_repository.get_equipment_with_history(
            equipment_id
        )

        if not equipment:
            raise ValueError("Equipment not found.")

        return {
            'equipment': self.format_equipment_data(equipment),
            'maintenance_requests': [
                self.format_request_history_data(request)
                for request in equipment.solicitudes.all()
            ],
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
            raise ValueError(
                f"Criticality '{criticality}' is not valid."
                f"Allowed values: {', '.join(VALID_CRITICALITIES)}."
            )

        equipment = self.equipment_repository.get_by_id(equipment_id)
        if not equipment:
            raise ValueError("Equipment not found.")

        if equipment.estado == 'dado_de_baja':
            raise ValueError(
                f"Equipment '{equipment.nombre}' is decommissioned and cannot be modified."
            )

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

    # ── Module -> Helpers ────────────────────────────────────────────────

    @staticmethod
    def _validate_and_transform_field(
        data: dict, field_key: str,
        db_field: str, allow_empty: bool = False
    ) -> tuple:

        if field_key not in data:
            return None, None

        value = str(data[field_key]).strip()
        if not value and not allow_empty:
            raise ValueError(f"Field '{field_key}' cannot be empty.")
        return db_field, value
