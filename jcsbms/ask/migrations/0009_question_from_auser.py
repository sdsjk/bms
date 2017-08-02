# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobileapp', '0004_auto_20160328_1100'),
        ('ask', '0008_auto_20160411_1043'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='from_auser',
            field=models.ForeignKey(to='mobileapp.AppUser', null=True),
        ),
    ]
