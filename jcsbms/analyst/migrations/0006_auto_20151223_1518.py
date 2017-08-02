# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyst', '0005_auto_20151223_1517'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analyst',
            name='brief',
            field=models.CharField(max_length=500),
        ),
    ]
