# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ask', '0006_auto_20160407_1801'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='is_closed',
        ),
        migrations.AddField(
            model_name='question',
            name='status',
            field=models.SmallIntegerField(default=0),
        ),
    ]
