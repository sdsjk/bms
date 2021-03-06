# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-01 03:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lottery', '0018_auto_20160512_1217'),
        ('mobileapp', '0007_portal'),
    ]

    operations = [
        migrations.CreateModel(
            name='LiveVedio',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('chargeable', models.BooleanField()),
                ('url', models.CharField(max_length=200)),
                ('location', models.SmallIntegerField(choices=[(1, '\u5317\u4eac'), (2, '\u4e0a\u6d77')])),
                ('match_name', models.CharField(max_length=100)),
                ('guests', models.CharField(max_length=100)),
                ('match', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lottery.Match')),
                ("cost", models.IntegerField(null=True)),
            ],
        ),
    ]
