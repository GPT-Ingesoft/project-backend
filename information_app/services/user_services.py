import re
from django.db import transaction

from information_app.repositories.user_repository import UserRepository
from information_app.services.services_utils import format_user_data, validate_required_fields

VALID_ROLES        = {'docente', 'laboratorista', 'tecnico'}
BASE_FIELDS        = {'name', 'email', 'role'}
TECHNICIAN_FIELDS  = {'specialty', 'contact'}
MIN_NAME_LENGTH    = 2
EMAIL_REGEX = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

class UserServices:
    def __init__(self):
        self.user_repository = UserRepository()

    # ── Module -> User registration ────────────────────────────────────────────
    @transaction.atomic
    def register_user(self, data: dict) -> dict:
        validate_required_fields(data, BASE_FIELDS)

        name      = data['name'].strip()
        email     = data['email'].strip().lower()
        role      = data['role'].strip().lower()
        specialty = None
        contact   = None

        if len(name) < MIN_NAME_LENGTH:
            raise ValueError("Name must be at least 2 characters long.")

        if role not in VALID_ROLES:
            raise ValueError(
                f"Role '{role}' is not valid. "
                f"Allowed roles: {', '.join(VALID_ROLES)}."
            )

        if self.user_repository.email_exists(email):
            raise ValueError(f"Email '{email}' is already registered. Please choose another.")

        if role == 'tecnico':
            validate_required_fields(data, TECHNICIAN_FIELDS)
            specialty = data['specialty'].strip()
            contact   = data['contact'].strip()

        user = self.user_repository.create_user(name=name, email=email, role=role)

        if role == 'tecnico':
            self.user_repository.create_technician(user=user, specialty=specialty, contact=contact)

        return format_user_data(user)

    # ── Module -> Profile Management ────────────────────────────────────────────
    @staticmethod
    def validate_profile_data(data: dict) -> None:
        validate_required_fields(data, ['name', 'email'])

        name = data['name'].strip()
        email = data['email'].strip().lower()

        if len(name) < MIN_NAME_LENGTH:
            raise ValueError(
                f"Name must be at least {MIN_NAME_LENGTH} characters long."
            )

        if not re.match(EMAIL_REGEX, email):
            raise ValueError(
                "Email format is invalid."
            )

    @transaction.atomic
    def update_own_profile(self, user, data: dict) -> dict:

        self.validate_profile_data(data)

        name = data['name'].strip()
        email = data['email'].strip().lower()

        if self.user_repository.email_exists_for_other_user(
            email,
            user.id
        ):
            raise ValueError(
                f"Email '{email}' is already registered."
            )

        user = self.user_repository.update_profile(
            user=user,
            name=name,
            email=email
        )

        return format_user_data(user)

    # ── Module -> User management ─────────────────────────────────────────
    def assign_role(self, user_id: int, role: str) -> dict:
        if role not in VALID_ROLES:
            raise ValueError(
                f"Role '{role}' is not valid. "
                f"Allowed roles: {', '.join(VALID_ROLES)}."
            )

        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found.")

        user = self.user_repository.update_role(user, role)
        return format_user_data(user)

    def change_status(self, user_id: int, active: bool) -> dict:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found.")

        user = self.user_repository.update_status(user, active)
        return format_user_data(user)

    def verify_access(self, user_id: int) -> dict:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found.")

        if not user.activo:
            raise PermissionError("Your account is deactivated. Please contact the lab technician.")

        return format_user_data(user)

    def list_users(self) -> list:
        users = self.user_repository.get_all()
        return [format_user_data(u) for u in users]

    # ── Module -> Helpers ────────────────────────────────────────────

    @staticmethod
    def is_lab_technician(user) -> bool:
        return user.rol == 'laboratorista'

    @staticmethod
    def is_teacher(user) -> bool:
        return user.rol == 'docente'

    @staticmethod
    def is_technician(user) -> bool:
        return user.rol == 'tecnico'
