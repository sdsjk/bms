# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jcs', '0007_auto_20160330_1841'),
    ]

    operations = [
        migrations.AddField(
            model_name='letter',
            name='invisible',
            field=models.BooleanField(default=False),
        ),
    ]
