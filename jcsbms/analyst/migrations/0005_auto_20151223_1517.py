# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyst', '0004_analyst_followers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analyst',
            name='brief',
            field=models.CharField(max_length=500, verbose_name='\u7b80\u8981'),
        ),
    ]
