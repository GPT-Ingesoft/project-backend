from django.utils import timezone

from information_app.models import Equipo, Intervencion

class EquipmentRepository:

    # ── Query operations ───────────────────────────────────────────────────────
    def get_by_id(self, equipment_id: int):
        return Equipo.objects.filter(id=equipment_id).first()

    def get_all(self):
        return Equipo.objects.all().order_by('nombre')

    def inventory_code_exists(self, inventory_code: str) -> bool:
        return Equipo.objects.filter(codigo_inventario=inventory_code).exists()

    def serial_number_exists(self, serial_number: str) -> bool:
        return Equipo.objects.filter(numero_serie=serial_number).exists()

    # ── Write operations ───────────────────────────────────────────────────────
    def create(self, name: str, inventory_code: str, model: str, brand: str,
               serial_number: str, location: str, status: str, criticality: str) -> Equipo:

        return Equipo.objects.create(
            nombre=name,
            codigo_inventario=inventory_code,
            modelo=model,
            marca=brand,
            numero_serie=serial_number,
            ubicacion=location,
            estado=status,
            criticidad=criticality,
        )

    def decommission(self, equipment: Equipo, reason: str) -> Equipo:
        equipment.estado = 'dado_de_baja'
        equipment.motivo_baja = reason
        equipment.fecha_baja = timezone.now()
        equipment.save()
        return equipment

    def update_criticality(self, equipment: Equipo, criticality: str) -> Equipo:
        equipment.criticidad = criticality
        equipment.save()
        return equipment

    def get_equipment_with_history(self, equipment_id: int):
        return (
            Equipo.objects
            .prefetch_related(
                'solicitudes',
                'solicitudes__intervenciones',
                'solicitudes__intervenciones__tecnico',
                'solicitudes__intervenciones__tecnico__usuario',
                'solicitudes__asignaciones',
                'solicitudes__asignaciones__tecnico',
                'solicitudes__asignaciones__tecnico__usuario',
                'solicitudes__historial_estados',
            )
            .filter(id=equipment_id)
            .first()
        )

    def create_intervention(self, solicitud, tecnico, descripcion: str, observaciones: str = None) -> Intervencion:
        return Intervencion.objects.create(
            solicitud=solicitud,
            tecnico=tecnico,
            descripcion=descripcion,
            observaciones=observaciones
        )
