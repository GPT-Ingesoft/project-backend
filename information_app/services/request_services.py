from django.db import transaction

from information_app.repositories.request_repository import RequestRepository


REASSIGNABLE_REQUEST_STATUSES = {'pendiente', 'en_proceso'}


class RequestServices:
    def __init__(self):
        self.request_repository = RequestRepository()

    @staticmethod
    def validate_technician_ids(data: dict) -> list[int]:
        technician_ids = data.get('technician_ids')

        if not isinstance(technician_ids, list) or not technician_ids:
            raise ValueError("Field 'technician_ids' is required and must be a non-empty list.")

        if not all(isinstance(technician_id, int) for technician_id in technician_ids):
            raise ValueError("Field 'technician_ids' must contain only integer values.")

        unique_ids = list(dict.fromkeys(technician_ids))
        if len(unique_ids) != len(technician_ids):
            raise ValueError("Field 'technician_ids' cannot contain duplicated values.")

        return unique_ids

    @staticmethod
    def format_technician_data(technician) -> dict:
        return {
            'id': technician.usuario.id,
            'name': technician.usuario.nombre,
            'email': technician.usuario.correo,
            'specialty': technician.especialidad,
            'contact': technician.contacto,
        }

    @staticmethod
    def format_request_assignment_data(request, technicians: list) -> dict:
        return {
            'request': {
                'id': request.id,
                'status': request.estado,
                'description': request.descripcion,
            },
            'assigned_technicians': [
                RequestServices.format_technician_data(technician)
                for technician in technicians
            ],
        }

    @transaction.atomic
    def reassign_technicians(self, request_id: int, data: dict) -> dict:
        technician_ids = self.validate_technician_ids(data)

        request = self.request_repository.get_by_id(request_id)
        if not request:
            raise ValueError("Request not found.")

        if request.estado not in REASSIGNABLE_REQUEST_STATUSES:
            raise ValueError(
                "Technicians can only be reassigned when the request status is "
                "'pendiente' or 'en_proceso'."
            )

        technicians = self.request_repository.get_technicians_by_ids(technician_ids)
        found_ids = {technician.usuario.id for technician in technicians}
        missing_ids = sorted(set(technician_ids) - found_ids)

        if missing_ids:
            raise ValueError(
                f"Technician users not found: {', '.join(map(str, missing_ids))}."
            )

        self.request_repository.replace_assigned_technicians(request, technicians)

        return self.format_request_assignment_data(request, technicians)
