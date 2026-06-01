from ..models import Usuario, Tecnico

class UsuarioRepository:
    
    # ── Escritura ──────────────────────────────────────────────────────────────
    def crear_usuario(self, nombre: str, correo: str, rol: str) -> Usuario:
        return Usuario.objects.create(nombre=nombre, correo=correo, rol=rol)
    
    def crear_tecnico(self, usuario: Usuario, especialidad: str, contacto: str) -> Tecnico:
        return Tecnico.objects.create(usuario=usuario, especialidad=especialidad, contacto=contacto)    
    
    # ── Consultas ──────────────────────────────────────────────────────────────
    def existe_correo(self, correo: str) -> bool:
        return Usuario.objects.filter(correo=correo).exists()
    
    def buscar_usuario_activo_por_correo(self, correo: str):
        if Usuario.objects.filter(correo=correo, activo=True).exists():
            return Usuario.objects.get(correo=correo, activo=True)
        
        return None

    def buscar_usuario_activo_por_id(self, user_id: int):
        if Usuario.objects.filter(id=user_id, activo=True).exists():
            return Usuario.objects.get(id=user_id, activo=True)
        
        return None