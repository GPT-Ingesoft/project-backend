import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('information_app', '0005_mantenimiento_preventivo'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitud',
            name='datos_equipo_solicitado',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='solicitud',
            name='equipo',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='solicitudes',
                to='information_app.equipo',
            ),
        ),
    ]
