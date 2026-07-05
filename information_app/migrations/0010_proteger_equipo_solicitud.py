import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('information_app', '0009_unificar_config_laboratorio'),
    ]

    operations = [
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
    ]
