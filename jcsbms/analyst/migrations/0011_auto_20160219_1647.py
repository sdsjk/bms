# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyst', '0010_apply'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apply',
            name='handle_status',
            field=models.SmallIntegerField(default=0),
        ),
    ]
