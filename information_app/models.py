from django.db import models

# =============================================================================
# MÓDULO 2: Gestión de Usuarios y Control de Acceso
# =============================================================================

class Usuario(models.Model):
    ROL_CHOICES = [
        ('docente', 'Docente'),
        ('laboratorista', 'Laboratorista'),
        ('tecnico', 'Técnico'),
    ]

    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    rol = models.CharField(max_length=50, choices=ROL_CHOICES, default='docente')
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'usuario'

    def __str__(self):
        return f"{self.nombre} ({self.rol})"


class Tecnico(models.Model):
    especialidad = models.CharField(max_length=100)
    contacto = models.CharField(max_length=100)

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='perfil_tecnico'
    )

    class Meta:
        db_table = 'tecnico'

    def __str__(self):
        return f"Técnico: {self.usuario.nombre} — {self.especialidad}"

# =============================================================================
# MÓDULO 1: Gestión de Equipos
# =============================================================================

class Equipo(models.Model):
    ESTADO_CHOICES = [
        ('operativo', 'Operativo'),
        ('en_mantenimiento', 'En Mantenimiento'),
        ('fuera_de_servicio', 'Fuera de Servicio'),
        ('dado_de_baja', 'Dado de Baja'),
    ]

    CRITICIDAD_CHOICES = [
        ('alta', 'Alta'),
        ('media', 'Media'),
        ('baja', 'Baja'),
    ]

    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    codigo_inventario = models.CharField(max_length=50, unique=True)
    modelo = models.CharField(max_length=100)
    marca = models.CharField(max_length=100)
    numero_serie = models.CharField(max_length=100, unique=True)
    ubicacion = models.CharField(max_length=100)
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='operativo')
    criticidad = models.CharField(max_length=50, choices=CRITICIDAD_CHOICES, default='media')
    motivo_baja = models.TextField(null=True, blank=True)
    fecha_baja = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'equipo'

    def __str__(self):
        return f"{self.nombre} [{self.get_estado_display()}]"

# =============================================================================
# MÓDULO 3: Gestión de Solicitudes de Mantenimiento
# =============================================================================

class HorarioAtencion(models.Model):
    DIA_CHOICES = [
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sábado'),
    ]

    id = models.AutoField(primary_key=True)
    laboratorio = models.CharField(max_length=100)
    dia = models.CharField(max_length=20, choices=DIA_CHOICES)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    disponible = models.BooleanField(default=True)

    class Meta:
        db_table = 'horario_atencion'

    def __str__(self):
        return f"{self.laboratorio} — {self.get_dia_display()} {self.hora_inicio}–{self.hora_fin}"

class Solicitud(models.Model):
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
    ]

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]

    id = models.AutoField(primary_key=True)
    descripcion = models.TextField(
        help_text='Diagnóstico inicial del problema reportado por el usuario.'
    )

    prioridad = models.CharField(max_length=50, choices=PRIORIDAD_CHOICES, default='media')
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha y hora en que la solicitud fue completada o cancelada.',
    )

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='solicitudes')

    equipo = models.ForeignKey(
        Equipo,
        on_delete=models.CASCADE, related_name='solicitudes',
        null=True, blank=True
    )

    datos_equipo_solicitado = models.JSONField(
        null=True, blank=True
    )

    horario_agendado = models.ForeignKey(
        HorarioAtencion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitudes'
    )

    class Meta:
        db_table = 'solicitud'

    def __str__(self):
        eq = self.equipo.nombre if self.equipo else "Sin Equipo"
        return f"Solicitud #{self.id} — {eq} [{self.get_estado_display()}]"

class HistorialEstadoSolicitud(models.Model):

    id = models.AutoField(primary_key=True)
    estado_anterior = models.CharField(max_length=50)
    estado_nuevo = models.CharField(max_length=50)
    motivo = models.TextField(
        help_text='Razón del cambio de estado. Obligatorio en cambios manuales.'
    )

    fecha_cambio = models.DateTimeField(auto_now_add=True)

    solicitud = models.ForeignKey(
        Solicitud,
        on_delete=models.CASCADE,
        related_name='historial_estados'
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cambios_estado_realizados'
    )

    class Meta:
        db_table = 'historial_estado_solicitud'
        ordering = ['-fecha_cambio']

    def __str__(self):
        return f"Solicitud #{self.solicitud.id}: {self.estado_anterior} → {self.estado_nuevo}"

class Anexo(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.TextField(
        help_text='Descripción del contexto o propósito de los archivos adjuntos.'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE, related_name='anexos')
    responsable = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='anexos_creados'
    )

    class Meta:
        db_table = 'anexo'

    def __str__(self):
        return f"Anexo #{self.id} — Solicitud #{self.solicitud.id}"

class Adjunto(models.Model):
    TIPO_CHOICES = [
        ('imagen', 'Imagen'),
        ('documento', 'Documento'),
        ('video', 'Video'),
        ('otro', 'Otro'),
    ]

    id = models.AutoField(primary_key=True)
    nombre_archivo = models.CharField(max_length=255)
    archivo = models.FileField(upload_to='adjuntos/%Y/%m/%d/')
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='otro')
    tamanio_bytes = models.PositiveIntegerField()
    fecha_carga = models.DateTimeField(auto_now_add=True)

    anexo = models.ForeignKey(Anexo, on_delete=models.CASCADE, related_name='adjuntos')

    class Meta:
        db_table = 'adjunto'

    def __str__(self):
        return self.nombre_archivo

class Asignacion(models.Model):

    id = models.AutoField(primary_key=True)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)

    solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE, related_name='asignaciones')
    tecnico = models.ForeignKey(Tecnico, on_delete=models.CASCADE, related_name='asignaciones')

    class Meta:
        db_table = 'asignacion'
        unique_together = ('solicitud', 'tecnico')

    def __str__(self):
        return f"{self.tecnico} → Solicitud #{self.solicitud.id}"

class Intervencion(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.TextField(help_text='Descripción de la intervención realizada al equipo.')
    observaciones = models.TextField(null=True, blank=True)
    fecha_intervencion = models.DateTimeField(auto_now_add=True)

    solicitud = models.ForeignKey(
        Solicitud,
        on_delete=models.CASCADE,
        related_name='intervenciones'
    )

    tecnico = models.ForeignKey(
        Tecnico,
        on_delete=models.SET_NULL,
        null=True,
        related_name='intervenciones'
    )

    class Meta:
        db_table = 'intervencion'
        ordering = ['-fecha_intervencion']

    def __str__(self):
        return f"Intervención #{self.id} — Solicitud #{self.solicitud.id}"

# =============================================================================
# MÓDULO 4: Notificaciones del Sistema
# =============================================================================

class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('mantenimiento_programado', 'Mantenimiento Programado'),
        ('asignacion_tecnico', 'Asignación de Técnico'),
        ('cambio_estado', 'Cambio de Estado'),
        ('mantenimiento_preventivo', 'Mantenimiento Preventivo'),
        ('otro', 'Otro'),
    ]

    id = models.AutoField(primary_key=True)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='otro')
    fecha_envio = models.DateTimeField(auto_now_add=True)

    solicitud = models.ForeignKey(
        Solicitud,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notificaciones'
    )
    destinatarios = models.ManyToManyField(
        Usuario,
        through='NotificacionUsuario',
        related_name='notificaciones_recibidas'
    )

    class Meta:
        db_table = 'notificacion'
        ordering = ['-fecha_envio']

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.mensaje[:60]}"

class NotificacionUsuario(models.Model):
    leida = models.BooleanField(default=False)
    fecha_lectura = models.DateTimeField(null=True, blank=True)

    notificacion = models.ForeignKey(Notificacion, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    class Meta:
        db_table = 'notificacion_usuario'
        unique_together = ('notificacion', 'usuario')

    def __str__(self):
        estado = 'leída' if self.leida else 'no leída'
        return f"Notif #{self.notificacion.id} → {self.usuario.nombre} ({estado})"
