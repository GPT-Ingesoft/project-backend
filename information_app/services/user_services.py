import re
from django.db import transaction
from information_app.repositories.user_repository import UserRepository
from information_app.services.services_utils import (
    format_user_data,
    validate_required_fields,
)

VALID_ROLES       = {'docente', 'laboratorista', 'tecnico'}
BASE_FIELDS       = {'name', 'email', 'role'}
TECHNICIAN_FIELDS = {'specialty', 'contact'}
MIN_NAME_LENGTH   = 2
EMAIL_REGEX       = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'


class UserServices:
    def __init__(self):
        self.user_repository = UserRepository()

    # ── Registro ────────────────────────────────────────────────────────────
    @transaction.atomic
    def register_user(self, data: dict) -> dict:
        validate_required_fields(data, BASE_FIELDS)

        name      = data['name'].strip()
        email     = data['email'].strip().lower()
        role      = data['role'].strip().lower()

        if len(name) < MIN_NAME_LENGTH:
            raise ValueError(f"Name must be at least {MIN_NAME_LENGTH} characters long.")
        if role not in VALID_ROLES:
            raise ValueError(f"Role '{role}' is not valid. Allowed: {', '.join(VALID_ROLES)}.")
        if self.user_repository.email_exists(email):
            raise ValueError(f"Email '{email}' is already registered.")

        specialty = None
        contact   = None
        if role == 'tecnico':
            validate_required_fields(data, TECHNICIAN_FIELDS)
            specialty = data['specialty'].strip()
            contact   = data['contact'].strip()

        user = self.user_repository.create_user(name=name, email=email, role=role)
        if role == 'tecnico':
            self.user_repository.create_technician(user=user, specialty=specialty, contact=contact)
        return format_user_data(user)

    # ── Perfil ──────────────────────────────────────────────────────────────

    @transaction.atomic
    def update_own_profile(self, user, data: dict) -> dict:
        validate_required_fields(data, ['name', 'email'])
        name  = data['name'].strip()
        email = data['email'].strip().lower()

        if len(name) < MIN_NAME_LENGTH:
            raise ValueError(f"Name must be at least {MIN_NAME_LENGTH} characters long.")
        if not re.match(EMAIL_REGEX, email):
            raise ValueError("Email format is invalid.")
        if self.user_repository.email_exists_for_other_user(email, user.id):
            raise ValueError(f"Email '{email}' is already registered.")

        user = self.user_repository.update(user, nombre=name, correo=email)
        self.user_repository.registrar_actividad(
            usuario=user,
            tipo='actualizacion_perfil',
            descripcion=f"El usuario actualizó su perfil.",
        )
        return format_user_data(user)

    # ── Gestión de usuarios ─────────────────────────────────────────────────

    def assign_role(self, user_id: int, role: str, data: dict | None = None) -> dict:
        if role not in VALID_ROLES:
            raise ValueError(f"Role '{role}' is not valid. Allowed: {', '.join(VALID_ROLES)}.")
        data = data or {}
        user = self._get_or_fail(user_id)
        user = self.user_repository.update(user, rol=role)
        if role == 'tecnico':
            has_technician_data = all(
                data.get(field) is not None and str(data.get(field)).strip()
                for field in TECHNICIAN_FIELDS
            )
            if has_technician_data:
                specialty = data['specialty'].strip()
                contact = data['contact'].strip()
                if hasattr(user, 'perfil_tecnico'):
                    technician = user.perfil_tecnico
                    self.user_repository.update(
                        technician,
                        especialidad=specialty,
                        contacto=contact,
                    )
                else:
                    self.user_repository.create_technician(
                        user=user,
                        specialty=specialty,
                        contact=contact,
                    )
        else:
            if hasattr(user, 'perfil_tecnico'):
                user.perfil_tecnico.delete()
        self.user_repository.registrar_actividad(
            usuario=user,
            tipo='asignacion_rol',
            descripcion=f"Se asignó el rol '{role}' al usuario.",
        )
        return format_user_data(user)

    def change_status(self, user_id: int, active: bool) -> dict:
        user = self._get_or_fail(user_id)
        user = self.user_repository.update(user, activo=active)
        estado = 'activada' if active else 'desactivada'
        self.user_repository.registrar_actividad(
            usuario=user,
            tipo='cambio_estado_cuenta',
            descripcion=f"La cuenta del usuario fue {estado}.",
        )
        return format_user_data(user)

    def verify_access(self, user_id: int) -> dict:
        user = self._get_or_fail(user_id)
        if not user.activo:
            raise PermissionError("Your account is deactivated. Contact the lab technician.")
        return format_user_data(user)

    def list_users(self) -> list:
        return [format_user_data(u) for u in self.user_repository.get_all()]

    def get_historial_actividad(self, user_id: int) -> list:
        self._get_or_fail(user_id)
        registros = self.user_repository.get_historial_actividad(user_id)
        return [
            {
                'id':          r.id,
                'tipo':        r.tipo,
                'descripcion': r.descripcion,
                'fecha':       r.fecha.isoformat(),
            }
            for r in registros
        ]

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def is_lab_technician(user) -> bool:
        return user.rol == 'laboratorista'

    @staticmethod
    def is_technician(user) -> bool:
        return user.rol == 'tecnico'

    def _get_or_fail(self, user_id: int):
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found.")
        return user
