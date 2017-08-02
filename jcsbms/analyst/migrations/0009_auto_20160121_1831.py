# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyst', '0008_auto_20160121_1734'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analyst',
            name='author_name',
            field=models.CharField(max_length=16, unique=True, null=True, editable=False),
        ),
    ]
