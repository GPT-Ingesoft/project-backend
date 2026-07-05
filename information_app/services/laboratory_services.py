from django.utils.dateparse import parse_time

from information_app.repositories.laboratory_repository import LaboratoryRepository
from information_app.services.services_utils import validate_required_fields


VALID_DAYS = {'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado'}


class LaboratoryServices:
    def __init__(self):
        self.repository = LaboratoryRepository()

    def list_laboratories(self) -> list:
        return [self._format_laboratory(lab, include_schedules=True)
                for lab in self.repository.get_all(order_by='nombre')]

    def get_laboratory(self, laboratory_id: int) -> dict:
        lab = self.repository.get_laboratory_with_schedules(laboratory_id)
        if not lab:
            raise ValueError("Laboratorio no encontrado.")
        return self._format_laboratory(lab, include_schedules=True)

    def create_laboratory(self, data: dict) -> dict:
        validate_required_fields(data, ['name'])
        name = str(data['name']).strip()
        if self.repository.get_by_name(name):
            raise ValueError(f"El laboratorio '{name}' ya existe.")
        lab = self.repository.create(
            nombre=name,
            ubicacion=str(data.get('location', '')).strip(),
            descripcion=str(data.get('description', '')).strip(),
            activo=bool(data.get('active', True)),
        )
        return self._format_laboratory(lab, include_schedules=True)

    def update_laboratory(self, laboratory_id: int, data: dict) -> dict:
        lab = self.repository.get_by_id(laboratory_id)
        if not lab:
            raise ValueError("Laboratorio no encontrado.")

        updates = {}
        if 'name' in data:
            name = str(data['name']).strip()
            if not name:
                raise ValueError("El campo 'name' no puede estar vacio.")
            existing = self.repository.get_by_name(name)
            if existing and existing.id != lab.id:
                raise ValueError(f"El laboratorio '{name}' ya existe.")
            updates['nombre'] = name
        if 'location' in data:
            updates['ubicacion'] = str(data['location']).strip()
        if 'description' in data:
            updates['descripcion'] = str(data['description']).strip()
        if 'active' in data:
            if not isinstance(data['active'], bool):
                raise ValueError("El campo 'active' debe ser true o false.")
            updates['activo'] = data['active']
        if not updates:
            raise ValueError("No hay campos validos para actualizar.")

        lab = self.repository.update(lab, **updates)
        if 'nombre' in updates:
            lab.horarios.update(laboratorio=updates['nombre'])
        return self._format_laboratory(lab, include_schedules=True)

    def delete_laboratory(self, laboratory_id: int) -> None:
        lab = self.repository.get_laboratory_with_schedules(laboratory_id)
        if not lab:
            raise ValueError("Laboratorio no encontrado.")
        if lab.horarios.exists():
            raise ValueError("No se puede eliminar un laboratorio con horarios asociados.")
        self.repository.delete_instance(lab)

    def list_schedules(self, laboratory_id=None) -> list:
        return [self._format_schedule(schedule)
                for schedule in self.repository.get_schedules(laboratory_id)]

    def get_schedule(self, schedule_id: int) -> dict:
        schedule = self.repository.get_schedule_by_id(schedule_id)
        if not schedule:
            raise ValueError("Horario no encontrado.")
        return self._format_schedule(schedule)

    def create_schedule(self, data: dict) -> dict:
        schedule_data = self._clean_schedule_data(data, partial=False)
        schedule = self.repository.create_schedule(**schedule_data)
        return self._format_schedule(schedule)

    def update_schedule(self, schedule_id: int, data: dict) -> dict:
        schedule = self.repository.get_schedule_by_id(schedule_id)
        if not schedule:
            raise ValueError("Horario no encontrado.")
        updates = self._clean_schedule_data(data, partial=True)
        if not updates:
            raise ValueError("No hay campos validos para actualizar.")
        schedule = self.repository.update(schedule, **updates)
        return self._format_schedule(schedule)

    def delete_schedule(self, schedule_id: int) -> None:
        schedule = self.repository.get_schedule_by_id(schedule_id)
        if not schedule:
            raise ValueError("Horario no encontrado.")
        if schedule.solicitudes.exists():
            raise ValueError("No se puede eliminar un horario asociado a solicitudes.")
        self.repository.delete_schedule(schedule)

    def _clean_schedule_data(self, data: dict, partial: bool) -> dict:
        if not partial:
            validate_required_fields(data, ['day', 'start_time', 'end_time'])

        updates = {}
        if 'laboratory_id' in data:
            lab = self.repository.get_by_id(data['laboratory_id'])
            if not lab:
                raise ValueError("Laboratorio no encontrado.")
            updates['laboratorio_ref'] = lab
            updates['laboratorio'] = lab.nombre
        elif not partial or 'laboratory' in data:
            lab_name = str(data.get('laboratory', '')).strip()
            if not lab_name:
                raise ValueError("Debe indicar 'laboratory_id' o 'laboratory'.")
            lab = self.repository.get_by_name(lab_name)
            updates['laboratorio_ref'] = lab
            updates['laboratorio'] = lab.nombre if lab else lab_name

        if 'day' in data:
            day = str(data['day']).strip().lower()
            if day not in VALID_DAYS:
                raise ValueError(f"Dia '{day}' no es valido.")
            updates['dia'] = day
        if 'start_time' in data:
            updates['hora_inicio'] = self._parse_time(data['start_time'], 'start_time')
        if 'end_time' in data:
            updates['hora_fin'] = self._parse_time(data['end_time'], 'end_time')
        if 'available' in data:
            if not isinstance(data['available'], bool):
                raise ValueError("El campo 'available' debe ser true o false.")
            updates['disponible'] = data['available']
        elif not partial:
            updates['disponible'] = True

        start = updates.get('hora_inicio')
        end = updates.get('hora_fin')
        if start and end and start >= end:
            raise ValueError("La hora de fin debe ser posterior a la hora de inicio.")
        return updates

    @staticmethod
    def _parse_time(value, field_name: str):
        parsed = parse_time(str(value))
        if not parsed:
            raise ValueError(f"El campo '{field_name}' debe tener formato HH:MM.")
        return parsed

    @staticmethod
    def _format_laboratory(lab, include_schedules=False) -> dict:
        data = {
            'id': lab.id,
            'name': lab.nombre,
            'location': lab.ubicacion,
            'description': lab.descripcion,
            'active': lab.activo,
            'created_at': lab.fecha_creacion.isoformat(),
        }
        if include_schedules:
            data['schedules'] = [
                LaboratoryServices._format_schedule(schedule)
                for schedule in lab.horarios.all()
            ]
        return data

    @staticmethod
    def _format_schedule(schedule) -> dict:
        return {
            'id': schedule.id,
            'laboratory': schedule.laboratorio,
            'laboratory_id': schedule.laboratorio_ref_id,
            'day': schedule.dia,
            'day_display': schedule.get_dia_display(),
            'start_time': schedule.hora_inicio.isoformat(),
            'end_time': schedule.hora_fin.isoformat(),
            'available': schedule.disponible,
        }
