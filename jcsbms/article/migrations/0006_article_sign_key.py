# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0005_auto_20151127_1321'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='sign_key',
            field=models.CharField(default=b'', max_length=32),
        ),
    ]
