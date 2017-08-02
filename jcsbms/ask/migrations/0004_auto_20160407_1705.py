# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ask', '0003_auto_20160407_1514'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='unread',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='reply',
            name='unread',
            field=models.BooleanField(default=True),
        ),
    ]
