# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyst', '0011_auto_20160219_1647'),
        ('jcs', '0005_auto_20160329_1244'),
    ]

    operations = [
        migrations.AddField(
            model_name='letter',
            name='to_author',
            field=models.ForeignKey(blank=True, to='analyst.Analyst', null=True),
        ),
    ]
