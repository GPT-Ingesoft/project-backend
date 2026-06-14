from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Agrega el campo fecha_cierre al modelo Solicitud.
    Necesario para RF_51: calcular el tiempo promedio de reparación
    usando las solicitudes en estado 'completada'.
    """

    dependencies = [
        ('information_app', '0002_remove_usuario_oauth_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitud',
            name='fecha_cierre',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text='Fecha y hora en que la solicitud fue completada o cancelada.',
            ),
        ),
    ]
