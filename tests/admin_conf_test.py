import sys
import types
import importlib.util
import pathlib
from datetime import datetime, timezone
from unittest.mock import MagicMock


def create_modules(*names):
    for name in names:
        sys.modules.setdefault(name, types.ModuleType(name))


class _Timezone:
    @staticmethod
    def now():
        return datetime(2024, 1, 1, tzinfo=timezone.utc)


create_modules(
    'django', 'django.db', 'django.db.models', 'django.utils',
    'information_app',
    'information_app.models',
    'information_app.repositories',
    'information_app.repositories.admin_repository',
    'information_app.repositories.config_repository',
    'information_app.repositories.repository_utils',
    'information_app.services',
)

sys.modules['django.utils'].timezone = _Timezone()

# Stub de ConfiguracionSistema
_config_model = MagicMock()
_config_model.CLAVE_UMBRAL_FUERA_DE_SERVICIO = 'umbral_dias_fuera_de_servicio'
sys.modules['information_app.models'].ConfiguracionSistema = _config_model

# Stubs de modelos que importa request_repository
for _name in ('Asignacion', 'Equipo', 'Solicitud', 'Tecnico',
              'HistorialEstadoSolicitud', 'Anexo', 'Adjunto', 'HorarioAtencion'):
    setattr(sys.modules['information_app.models'], _name, MagicMock())


# BaseRepository stub
class _BaseRepository:
    def get_model(self): ...


sys.modules['information_app.repositories.repository_utils'].BaseRepository = _BaseRepository
sys.modules['information_app.repositories.admin_repository'].AdminRepository = _BaseRepository
sys.modules['information_app.repositories.config_repository'].ConfigRepository = _BaseRepository

# Carga dinámica de AdminServices
_svc_path = (
    pathlib.Path(__file__).resolve().parent.parent
    / 'information_app' / 'services' / 'admin_services.py'
)
_spec = importlib.util.spec_from_file_location('information_app.services.admin_services', _svc_path)
_mod = importlib.util.module_from_spec(_spec)
_mod.__package__ = 'information_app.services'
sys.modules['information_app.services.admin_services'] = _mod
_spec.loader.exec_module(_mod)

AdminServices = _mod.AdminServices
UMBRAL_DIAS_DEFAULT = _mod.UMBRAL_DIAS_DEFAULT

# Ruta a request_repository para los tests de RF_36
_repo_path = (
    pathlib.Path(__file__).resolve().parent.parent
    / 'information_app' / 'repositories' / 'request_repository.py'
)

NOW = datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc)


def make_notification(notification_id, fecha_envio, tipo='otro', mensaje='msg'):
    n = MagicMock()
    n.id = notification_id
    n.fecha_envio = fecha_envio
    n.tipo = tipo
    n.get_tipo_display.return_value = tipo.replace('_', ' ').title()
    n.mensaje = mensaje
    n.solicitud = None
    n.destinatarios.all.return_value = []
    return n


def make_equipment(equipment_id, nombre, ubicacion='Lab 1', estado='operativo',
                   codigo='COD-01', total_fallas=None, motivo_baja=None,
                   fecha_baja=None, promedio_horas=None, dias_inactivo=None):
    # Todas las claves siempre presentes para que los formatters del servicio
    # no fallen con KeyError cuando el valor es None.
    return {
        'id':                equipment_id,
        'nombre':            nombre,
        'ubicacion':         ubicacion,
        'estado':            estado,
        'codigo_inventario': codigo,
        'total_fallas':      total_fallas,
        'motivo_baja':       motivo_baja,
        'fecha_baja':        fecha_baja,
        'promedio_horas':    promedio_horas,
        'dias_inactivo':     dias_inactivo,
    }


def make_admin_service(*, notifications=None, failure=None, repair=None,
                       out_of_service=None, active=None, maintenance=None,
                       decommissioned=None, threshold_stored=None):
    svc = AdminServices.__new__(AdminServices)

    repo = MagicMock()
    repo.get_notification_history.return_value = notifications or []
    repo.get_notification_by_id.return_value = None
    repo.get_failure_report.return_value = failure or []
    repo.get_repair_time_report.return_value = repair or []
    repo.get_out_of_service_equipment.return_value = out_of_service or []
    repo.get_active_equipment.return_value = active or []
    repo.get_maintenance_equipment.return_value = maintenance or []
    repo.get_decommissioned_equipment.return_value = decommissioned or []

    config_repo = MagicMock()
    config_repo.get_value.return_value = threshold_stored
    config_repo.set_value.return_value = MagicMock()

    svc.repo = repo
    svc.config_repo = config_repo
    return svc, repo, config_repo


def load_request_repository():
    spec = importlib.util.spec_from_file_location('rr', _repo_path)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = 'information_app.repositories'
    spec.loader.exec_module(mod)
    return mod.RequestRepository()