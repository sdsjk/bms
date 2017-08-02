# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyst', '0007_analyst_invisible'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analyst',
            name='author_name',
            field=models.CharField(max_length=16, unique=True, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='analyst',
            name='brief',
            field=models.CharField(max_length=60),
        ),
    ]
