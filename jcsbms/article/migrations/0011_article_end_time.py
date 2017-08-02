# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0010_auto_20160303_1750'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='end_time',
            field=models.DateTimeField(null=True),
        ),
    ]
