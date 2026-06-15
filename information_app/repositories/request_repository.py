from information_app.models import Asignacion, Solicitud, Tecnico


class RequestRepository:

    def get_by_id(self, request_id: int):
        return Solicitud.objects.filter(id=request_id).first()

    def get_technicians_by_ids(self, technician_ids: list[int]):
        return list(
            Tecnico.objects
            .select_related('usuario')
            .filter(usuario_id__in=technician_ids)
        )

    def replace_assigned_technicians(self, request: Solicitud, technicians: list[Tecnico]):
        Asignacion.objects.filter(solicitud=request).update(activa=False)

        assignments = []
        for technician in technicians:
            assignment, _ = Asignacion.objects.update_or_create(
                solicitud=request,
                tecnico=technician,
                defaults={'activa': True},
            )
            assignments.append(assignment)

        return assignments
