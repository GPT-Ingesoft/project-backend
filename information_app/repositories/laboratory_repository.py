from information_app.models import HorarioAtencion, Laboratorio
from information_app.repositories.repository_utils import BaseRepository


class LaboratoryRepository(BaseRepository):
    def get_model(self):
        return Laboratorio

    def get_by_name(self, name: str):
        return self.get_model().objects.filter(nombre__iexact=name).first()

    def get_laboratory_with_schedules(self, laboratory_id: int):
        return (
            self.get_model()
            .objects.prefetch_related('horarios')
            .filter(id=laboratory_id)
            .first()
        )

    def get_schedules(self, laboratory_id=None):
        qs = HorarioAtencion.objects.select_related('laboratorio_ref')
        if laboratory_id is not None:
            qs = qs.filter(laboratorio_ref_id=laboratory_id)
        return qs.order_by('laboratorio', 'dia', 'hora_inicio')

    def get_schedule_by_id(self, schedule_id: int):
        return (
            HorarioAtencion.objects
            .select_related('laboratorio_ref')
            .filter(id=schedule_id)
            .first()
        )

    def create_schedule(self, **kwargs):
        return HorarioAtencion.objects.create(**kwargs)

    def delete_schedule(self, schedule):
        schedule.delete()
