from information_app.models import Usuario, Tecnico, HistorialActividadUsuario
from information_app.repositories.repository_utils import BaseRepository

class UserRepository(BaseRepository):
    def get_model(self):
        return Usuario

    # ── Query operations ──────────────────────────────────────────

    def find_active_user_by_email(self, email):
        return self.get_model().objects.filter(correo=email, activo=True).first()

    def find_active_user_by_id(self, user_id):
        return self.get_model().objects.filter(id=user_id, activo=True).first()

    def email_exists(self, email: str) -> bool:
        return self.exists(correo=email)

    def email_exists_for_other_user(self, email: str, user_id: int) -> bool:
        return self.exists_excluding(user_id, correo=email)

    # ── Write operations ──────────────────────────────────────────

    def create_user(self, name: str, email: str, role: str) -> Usuario:
        return self.create(nombre=name, correo=email, rol=role)

    def create_technician(self, user: Usuario, specialty: str, contact: str) -> Tecnico:
        return Tecnico.objects.create(usuario=user, especialidad=specialty, contacto=contact)

    def get_all(self, order_by: str = None):
        return super().get_all(order_by='nombre')

    # ── Historial de actividad ────────────────────────────────────

    def registrar_actividad(self, usuario, tipo: str, descripcion: str):
        return HistorialActividadUsuario.objects.create(
            usuario=usuario,
            tipo=tipo,
            descripcion=descripcion,
        )

    def get_historial_actividad(self, user_id: int):
        return HistorialActividadUsuario.objects.filter(usuario_id=user_id)