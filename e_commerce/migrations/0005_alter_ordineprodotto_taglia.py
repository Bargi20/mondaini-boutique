# Generated by Django 5.1.4 on 2025-04-24 10:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('e_commerce', '0004_ordineprodotto_taglia_alter_prodotto_tipo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ordineprodotto',
            name='taglia',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='e_commerce.taglia'),
        ),
    ]
