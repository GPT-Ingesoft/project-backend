from ..models import Equipo
from django.utils import timezone

class EquipoRepository:

    def obtener_por_id(self, equipo_id: int):
        return Equipo.objects.filter(id=equipo_id).first()

    def listar_todos(self):
        return Equipo.objects.all().order_by('nombre')

    def dar_de_baja(self, equipo: Equipo, motivo: str) -> Equipo:
        equipo.estado = 'dado_de_baja'
        equipo.motivo_baja = motivo
        equipo.fecha_baja = timezone.now()
        equipo.save()
        return equipo

    def actualizar_criticidad(self, equipo: Equipo, criticidad: str) -> Equipo:
        equipo.criticidad = criticidad
        equipo.save()
        return equipo