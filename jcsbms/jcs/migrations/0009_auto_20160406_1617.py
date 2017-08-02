# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jcs', '0008_letter_invisible'),
    ]

    operations = [
        migrations.AlterField(
            model_name='letter',
            name='content',
            field=models.CharField(max_length=1018),
        ),
    ]
