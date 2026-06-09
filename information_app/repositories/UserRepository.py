from ..models import Usuario, Tecnico

class UserRepository:

    # ── Write operations ───────────────────────────────────────────────────────
    def create_user(self, name: str, email: str, role: str) -> Usuario:
        return Usuario.objects.create(nombre=name, correo=email, rol=role)

    def create_technician(self, user: Usuario, specialty: str, contact: str) -> Tecnico:
        return Tecnico.objects.create(usuario=user, especialidad=specialty, contacto=contact)

    # ── Query operations ───────────────────────────────────────────────────────
    def email_exists(self, email: str) -> bool:
        return Usuario.objects.filter(correo=email).exists()

    def find_active_user_by_email(self, email: str):
        if Usuario.objects.filter(correo=email, activo=True).exists():
            return Usuario.objects.get(correo=email, activo=True)
        return None

    def find_active_user_by_id(self, user_id: int):
        if Usuario.objects.filter(id=user_id, activo=True).exists():
            return Usuario.objects.get(id=user_id, activo=True)
        return None

    # ── User management ────────────────────────────────────────────────────────
    def get_by_id(self, user_id: int):
        return Usuario.objects.filter(id=user_id).first()

    def get_all(self):
        return Usuario.objects.all().order_by('nombre')

    def update_role(self, user: Usuario, role: str) -> Usuario:
        user.rol = role
        user.save()
        return user

    def update_status(self, user: Usuario, active: bool) -> Usuario:
        user.activo = active
        user.save()
        return user

    def update_profile(self, user: Usuario, name: str, email: str) -> Usuario:
        user.nombre = name
        user.correo = email
        user.save(update_fields=['nombre', 'correo'])
        return user

    def email_exists_for_other_user(self, email: str, user_id: int) -> bool:
        return Usuario.objects.filter(correo=email).exclude(id=user_id).exists()