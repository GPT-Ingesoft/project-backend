import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    RF_36 + RF_52.

    RF_36: cambia on_delete=CASCADE → PROTECT en las FK de Solicitud hacia
    Usuario y Equipo. Esto garantiza que eliminar un usuario o equipo no
    borre en cascada las solicitudes asociadas; Django lanzará ProtectedError
    antes de permitirlo.

    RF_52: crea el modelo ConfiguracionSistema para que el administrador pueda
    persistir el umbral de días de inactividad usado en el reporte de equipos
    fuera de servicio, en lugar de depender de un parámetro en cada petición.
    """

    dependencies = [
        ('information_app', '0006_solicitud_datos_equipo_solicitado'),
    ]

    operations = [
        # ── RF_36: proteger Solicitud de borrados en cascada ─────────────────
        migrations.AlterField(
            model_name='solicitud',
            name='usuario',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='solicitudes',
                to='information_app.usuario',
            ),
        ),
        migrations.AlterField(
            model_name='solicitud',
            name='equipo',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='solicitudes',
                to='information_app.equipo',
            ),
        ),
        # ── RF_52: tabla de configuración del sistema ────────────────────────
        migrations.CreateModel(
            name='ConfiguracionSistema',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('clave', models.CharField(max_length=100, unique=True)),
                ('valor', models.CharField(max_length=255)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'configuracion_sistema',
            },
        ),
    ]
