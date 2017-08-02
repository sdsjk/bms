# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ask', '0005_auto_20160407_1800'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reply',
            name='content',
            field=models.TextField(max_length=1018),
        ),
    ]
