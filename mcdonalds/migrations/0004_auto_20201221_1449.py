# Generated by Django 3.0.3 on 2020-12-21 06:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mcdonalds', '0003_auto_20201209_2057'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='storedemanddetails',
            name='store',
        ),
        migrations.AddField(
            model_name='customers',
            name='email',
            field=models.EmailField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='storedemanddetails',
            name='store_demand',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mcdonalds.StoreDemand'),
        ),
        migrations.AlterField(
            model_name='rawmaterial',
            name='material_id',
            field=models.AutoField(editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='rawmaterial',
            name='reorder_point',
            field=models.PositiveIntegerField(),
        ),
    ]
