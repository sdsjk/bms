# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ask', '0002_auto_20160407_1506'),
    ]

    operations = [
        migrations.RenameField(
            model_name='reply',
            old_name='user',
            new_name='poster',
        ),
        migrations.AddField(
            model_name='question',
            name='is_closed',
            field=models.BooleanField(default=False),
        ),
    ]
