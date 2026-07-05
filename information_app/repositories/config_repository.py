from information_app.models import ConfiguracionSistema
from information_app.repositories.repository_utils import BaseRepository

class ConfigRepository(BaseRepository):

    def get_model(self):
        return ConfiguracionSistema

    def get_value(self, clave: str):
        config = ConfiguracionSistema.objects.filter(clave=clave).first()
        return config.valor if config else None

    def set_value(self, clave: str, valor) -> ConfiguracionSistema:
        config, _ = ConfiguracionSistema.objects.update_or_create(
            clave=clave,
            defaults={'valor': str(valor)},
        )
        return config
      
