# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0004_auto_20151125_1540'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='invisible',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterUniqueTogether(
            name='articlelotteries',
            unique_together=set([('article', 'lottery')]),
        ),
    ]
