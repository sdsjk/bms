# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyst', '0002_auto_20151119_1331'),
    ]

    operations = [
        migrations.AddField(
            model_name='analyst',
            name='author_name',
            field=models.CharField(max_length=16, unique=True, null=True),
        ),
    ]
