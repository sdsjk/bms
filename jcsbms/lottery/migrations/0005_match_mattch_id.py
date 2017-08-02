# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lottery', '0004_auto_20151125_1352'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='mattch_id',
            field=models.CharField(default=b'', max_length=32),
        ),
    ]
