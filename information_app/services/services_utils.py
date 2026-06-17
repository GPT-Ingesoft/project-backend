# ── Helpers - Validators ─────────────────────────────────────────

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

# ── Helpers - Formatters ───────────────────────────────────────────────────────

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

def format_equipment_data(equipment) -> dict:
    return {
        'id':                equipment.id,
        'name':              equipment.nombre,
        'inventory_code':    equipment.codigo_inventario,
        'model':             equipment.modelo,
        'brand':             equipment.marca,
        'serial_number':     equipment.numero_serie,
        'location':          equipment.ubicacion,
        'status':            equipment.estado,
        'criticality':       equipment.criticidad,
        'decommission_reason': equipment.motivo_baja,
        'decommission_date': (
            equipment.fecha_baja.isoformat() if equipment.fecha_baja else None
        ),
        'created_at':        equipment.fecha_creacion.isoformat(),
    }
