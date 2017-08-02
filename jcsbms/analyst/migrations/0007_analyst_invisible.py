# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyst', '0006_auto_20151223_1518'),
    ]

    operations = [
        migrations.AddField(
            model_name='analyst',
            name='invisible',
            field=models.BooleanField(default=False),
        ),
    ]
