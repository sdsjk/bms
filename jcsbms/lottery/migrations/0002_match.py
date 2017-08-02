# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lottery', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('taskid', models.CharField(max_length=32, unique=True, null=True)),
                ('cup_name', models.CharField(max_length=16)),
                ('start_time', models.DateTimeField()),
                ('home_team', models.CharField(max_length=16)),
                ('away_team', models.CharField(max_length=16)),
                ('type', models.ForeignKey(to='lottery.Lotterytype')),
            ],
        ),
    ]
