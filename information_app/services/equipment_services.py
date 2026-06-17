from django.db import transaction
from information_app.repositories.equipment_repository import EquipmentRepository
from information_app.services.services_utils import (
    format_equipment_data,
    format_technician_data,
    validate_required_fields,
    validate_enum,
)

VALID_CRITICALITIES       = {'alta', 'media', 'baja'}
REQUIRED_EQUIPMENT_FIELDS = {
    'name', 'inventory_code', 'model',
    'brand', 'serial_number', 'location'
}

VALID_STATUSES            = {'operativo', 'en_mantenimiento', 'fuera_de_servicio'}

class EquipmentServices:
    def __init__(self):
        self.equipment_repository = EquipmentRepository()

    # ── Registro ────────────────────────────────────────────────────────────

    @transaction.atomic
    def register_equipment(self, data: dict) -> dict:
        validate_required_fields(data, REQUIRED_EQUIPMENT_FIELDS)

        name           = data['name'].strip()
        inventory_code = data['inventory_code'].strip()
        model          = data['model'].strip()
        brand          = data['brand'].strip()
        serial_number  = data['serial_number'].strip()
        location       = data['location'].strip()
        status        = validate_enum(
            data.get('status', 'operativo').strip().lower(),
            VALID_STATUSES,
            'Status'
        )

        criticality   = validate_enum(
            data.get('criticality', 'media').strip().lower(),
            VALID_CRITICALITIES,
            'Criticality'
        )

        if self.equipment_repository.inventory_code_exists(inventory_code):
            raise ValueError(f"Inventory code '{inventory_code}' is already registered.")
        if self.equipment_repository.serial_number_exists(serial_number):
            raise ValueError(f"Serial number '{serial_number}' is already registered.")

        equipment = self.equipment_repository.create(
                    nombre=name, codigo_inventario=inventory_code, modelo=model,
                    marca=brand, numero_serie=serial_number, ubicacion=location,
                    estado=status, criticidad=criticality,
                )
        return format_equipment_data(equipment)

    @transaction.atomic
    def update_equipment(self, equipment_id: int, data: dict) -> dict:
        equipment = self._get_or_fail(equipment_id)
        if equipment.estado == 'dado_de_baja':
            raise ValueError(f"Equipment '{equipment.nombre}' is decommissioned.")

        if 'serial_number' in data:
            raise ValueError("Field 'serial_number' cannot be modified.")

        fields_to_update = {}
        for field_key, db_field in [
            ('name', 'nombre'),
            ('inventory_code', 'codigo_inventario'),
            ('model', 'modelo'),
            ('brand', 'marca'),
            ('location', 'ubicacion'),
        ]:
            if field_key in data:
                value = str(data[field_key]).strip()
                if not value:
                    raise ValueError(f"Field '{field_key}' cannot be empty.")
                if field_key == 'inventory_code':
                    if self.equipment_repository.inventory_code_exists_for_other(
                        value,
                        equipment_id
                    ):

                        raise ValueError(f"Inventory code '{value}' is already registered.")
                fields_to_update[db_field] = value

        if 'status' in data:
            fields_to_update['estado'] = validate_enum(
                str(data['status']).strip().lower(), VALID_STATUSES, 'Status'
            )
        if 'criticality' in data:
            fields_to_update['criticidad'] = validate_enum(
                str(data['criticality']).strip().lower(), VALID_CRITICALITIES, 'Criticality'
            )

        if not fields_to_update:
            raise ValueError("No valid fields provided for update.")

        equipment = self.equipment_repository.update(equipment, **fields_to_update)
        return format_equipment_data(equipment)

    # ── Gestión ─────────────────────────────────────────────────────────────

    def list_equipment(self) -> list:
        return [format_equipment_data(e) for e in self.equipment_repository.get_all()]

    def get_equipment_history(self, equipment_id: int) -> dict:
        equipment = self.equipment_repository.get_equipment_with_history(equipment_id)
        if not equipment:
            raise ValueError("Equipment not found.")
        return {
            'equipment': format_equipment_data(equipment),
            'maintenance_requests': [
                self._format_request_history(req) for req in equipment.solicitudes.all()
            ],
        }

    def decommission_equipment(self, equipment_id: int, reason: str) -> dict:
        equipment = self._get_or_fail(equipment_id)
        if equipment.estado == 'dado_de_baja':
            raise ValueError(f"Equipment '{equipment.nombre}' is already decommissioned.")
        equipment = self.equipment_repository.decommission(equipment, reason)
        return format_equipment_data(equipment)

    def update_criticality(self, equipment_id: int, criticality: str) -> dict:
        validate_enum(criticality, VALID_CRITICALITIES, 'Criticality')
        equipment = self._get_or_fail(equipment_id)
        if equipment.estado == 'dado_de_baja':
            raise ValueError(f"Equipment '{equipment.nombre}' is decommissioned.")
        equipment = self.equipment_repository.update(equipment, criticidad=criticality)
        return format_equipment_data(equipment)

    def verify_availability(self, equipment_id: int) -> dict:
        equipment = self._get_or_fail(equipment_id)
        if equipment.estado == 'dado_de_baja':
            raise ValueError(
                f"Equipment '{equipment.nombre}' is decommissioned. Reason: {equipment.motivo_baja}"
            )
        return format_equipment_data(equipment)

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _get_or_fail(self, equipment_id: int):
        equipment = self.equipment_repository.get_by_id(equipment_id)
        if not equipment:
            raise ValueError("Equipment not found.")
        return equipment

    @staticmethod
    def _format_request_history(request) -> dict:
        return {
            'id':              request.id,
            'description':     request.descripcion,
            'priority':        request.prioridad,
            'status':          request.estado,
            'created_at':      request.fecha_creacion.isoformat(),
            'scheduled_attention': (
                {
                    'id': request.horario_agendado.id,
                    'laboratory': request.horario_agendado.laboratorio,
                    'day': request.horario_agendado.dia,
                    'start_time': request.horario_agendado.hora_inicio.isoformat(),
                    'end_time': request.horario_agendado.hora_fin.isoformat(),
                } if request.horario_agendado else None
            ),
            'assigned_technicians': [
                format_technician_data(a.tecnico) for a in request.asignaciones.all()
            ],
            'status_history': [
                {
                    'id': h.id,
                    'previous_status': h.estado_anterior,
                    'new_status': h.estado_nuevo,
                    'reason': h.motivo,
                    'changed_at': h.fecha_cambio.isoformat(),
                    'changed_by': (
                        {'id': h.usuario.id, 'name': h.usuario.nombre, 'email': h.usuario.correo}
                        if h.usuario else None
                    ),
                }
                for h in request.historial_estados.all()
            ],
            'interventions': [
                {
                    'id': i.id,
                    'description': i.descripcion,
                    'observations': i.observaciones,
                    'performed_at': i.fecha_intervencion.isoformat(),
                    'technician': format_technician_data(i.tecnico),
                }
                for i in request.intervenciones.all()
            ],
        }
