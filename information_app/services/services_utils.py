
def format_user_data(user) -> dict:
    return {
        'id':         user.id,
        'name':       user.nombre,
        'email':      user.correo,
        'role':       user.rol,
        'active':     user.activo,
        'created_at': user.fecha_creacion.isoformat(),
    }

def format_technician_data(technician) -> dict:
    if not technician:
        return None
    return {
        'id': technician.usuario.id,
        'name': technician.usuario.nombre,
        'email': technician.usuario.correo,
        'specialty': technician.especialidad,
        'contact': technician.contacto,
    }

def validate_required_fields(data: dict, fields: list) -> None:
    for field in fields:
        value = data.get(field)
        if value is None or str(value).strip() == '':
            raise ValueError(f"Field '{field}' is required and cannot be empty.")

def validate_enum(value: str, valid_values: set, field_name: str) -> str:
    if value not in valid_values:
        raise ValueError(
            f"{field_name} '{value}' is not valid. "
            f"Allowed values: {', '.join(sorted(valid_values))}."
        )
    return value
