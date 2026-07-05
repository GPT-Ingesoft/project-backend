import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
   
    dependencies = [
        ('information_app', '0006_solicitud_datos_equipo_solicitado'),
    ]

    operations = [
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
