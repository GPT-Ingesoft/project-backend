from ..repositories.UsuarioRepository import UsuarioRepository

from django.db import transaction

ROLES_VALIDOS = {'docente', 'laboratorista', 'tecnico'}
CAMPOS_BASE   = {'nombre', 'correo', 'rol'}
CAMPOS_TECNICO = {'especialidad', 'contacto'}

LONGITUD_NOMBRE_MINIMA = 2

class UsuarioServices:
    def __init__(self):
        self.usuario_repository = UsuarioRepository()

    @staticmethod
    def validar_datos_usuario(datos: dict, campos: list) -> None:
        for campo in campos:
            valor = datos.get(campo)
            if valor is None or str(valor).strip() == '':
                raise ValueError(f"El campo '{campo}' es obligatorio y no puede estar vacío.")

    @staticmethod
    def formato_datos_usuario(usuario) -> dict:
        return {
            'id':               usuario.id,
            'nombre':           usuario.nombre,
            'correo':           usuario.correo,
            'rol':              usuario.rol,
            'activo':           usuario.activo,
            'fecha_creacion':   usuario.fecha_creacion.isoformat(),
        }

    @transaction.atomic
    def registrar_usuario(self, datos: dict) -> dict:
        
        self.validar_datos_usuario(datos, CAMPOS_BASE)

        nombre = datos['nombre'].strip()
        correo = datos['correo'].strip().lower()
        rol = datos['rol'].strip().lower()
        especialidad = None
        contacto = None

        if len(nombre) < LONGITUD_NOMBRE_MINIMA:
            raise ValueError("El nombre debe tener al menos 2 caracteres.")
        
        if rol not in ROLES_VALIDOS:
            raise ValueError(f"El rol '{rol}' no es válido. Roles permitidos: {', '.join(ROLES_VALIDOS)}.")
        
        if self.usuario_repository.existe_correo(correo):
            raise ValueError(f"El correo '{correo}' ya está registrado. Por favor, elige otro.")
        
        if rol == 'tecnico':
            self.validar_datos_usuario(datos, CAMPOS_TECNICO)
            especialidad = datos['especialidad'].strip()
            contacto = datos['contacto'].strip()

        usuario = self.usuario_repository.crear_usuario(nombre=nombre, correo=correo, rol=rol)

        if rol == 'tecnico':
            self.usuario_repository.crear_tecnico(usuario=usuario, especialidad=especialidad, contacto=contacto)

        return self.formato_datos_usuario(usuario)


