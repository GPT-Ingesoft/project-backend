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

    @staticmethod
    def format_technician_data(technician) -> dict:
        if not technician:
            return None

        return {
            'id': technician.usuario.id,
            'name': technician.usuario.nombre,
            'email': technician.usuario.correo,
            'specialty': technician.especialidad,
            'contact': technician.contacto,
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
            'technician': EquipmentServices.format_technician_data(
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
                EquipmentServices.format_technician_data(
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