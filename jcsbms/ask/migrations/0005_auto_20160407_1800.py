# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ask', '0004_auto_20160407_1705'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='content',
            field=models.TextField(max_length=500),
        ),
        migrations.AlterField(
            model_name='reply',
            name='content',
            field=models.TextField(max_length=1000),
        ),
    ]
