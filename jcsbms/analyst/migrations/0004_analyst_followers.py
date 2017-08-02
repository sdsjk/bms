# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobileapp', '0001_initial'),
        ('analyst', '0003_analyst_author_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='analyst',
            name='followers',
            field=models.ManyToManyField(to='mobileapp.AppUser', through='mobileapp.Follow'),
        ),
    ]
