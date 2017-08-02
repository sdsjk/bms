# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0009_auto_20160222_1610'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='istop',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='article',
            name='top_time',
            field=models.DateTimeField(null=True),
        ),
    ]
