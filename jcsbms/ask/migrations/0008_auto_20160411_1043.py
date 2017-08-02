# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ask', '0007_auto_20160408_1440'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='grade',
            field=models.SmallIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='review',
            field=models.CharField(max_length=200, null=True),
        ),
    ]
