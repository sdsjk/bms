# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0007_auto_20160129_1749'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='origin',
            field=models.CharField(max_length=32, null=True),
        ),
    ]
