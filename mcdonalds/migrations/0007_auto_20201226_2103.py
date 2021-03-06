# Generated by Django 3.0.3 on 2020-12-26 13:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mcdonalds', '0006_auto_20201224_0851'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storedemand',
            name='store',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to='mcdonalds.Stores'),
        ),
        migrations.AlterField(
            model_name='storedemanddetails',
            name='prod_numbers',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='storedemanddetails',
            name='product',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to='mcdonalds.Products'),
        ),
        migrations.AlterField(
            model_name='storedemanddetails',
            name='store_demand',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='mcdonalds.StoreDemand'),
        ),
    ]
