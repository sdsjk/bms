# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyst', '0009_auto_20160121_1831'),
    ]

    operations = [
        migrations.CreateModel(
            name='Apply',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('real_name', models.CharField(max_length=4)),
                ('email', models.EmailField(max_length=100, null=True)),
                ('weichat', models.CharField(max_length=32, null=True)),
                ('mobile', models.CharField(max_length=11)),
                ('skill', models.CharField(max_length=100)),
                ('brief', models.CharField(max_length=320)),
                ('handle_status', models.SmallIntegerField(default=1)),
                ('handle_result', models.CharField(max_length=120, null=True)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
