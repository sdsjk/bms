# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-05 10:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lottery', '0009_auto_20160505_1229'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='lotterytypes',
            field=models.ManyToManyField(to='lottery.Lotterytype'),
        ),
    ]
