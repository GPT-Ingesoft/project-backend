import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('information_app', '0004_request_closing_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='MantenimientoPreventivo',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('descripcion', models.TextField()),
                ('fecha_programada', models.DateTimeField()),
                ('anticipacion_horas', models.PositiveIntegerField(default=24)),
                (
                    'estado',
                    models.CharField(
                        choices=[
                            ('programado', 'Programado'),
                            ('completado', 'Completado'),
                            ('cancelado', 'Cancelado'),
                        ],
                        default='programado',
                        max_length=20,
                    ),
                ),
                ('notificado_en', models.DateTimeField(blank=True, null=True)),
                (
                    'equipo',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='mantenimientos_preventivos',
                        to='information_app.equipo',
                    ),
                ),
                (
                    'tecnicos',
                    models.ManyToManyField(
                        blank=True,
                        related_name='mantenimientos_preventivos',
                        to='information_app.tecnico',
                    ),
                ),
            ],
            options={
                'db_table': 'mantenimiento_preventivo',
                'ordering': ['fecha_programada'],
            },
        ),
    ]
