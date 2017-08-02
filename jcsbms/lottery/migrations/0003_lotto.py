# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lottery', '0002_match'),
    ]

    operations = [
        migrations.CreateModel(
            name='Lotto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('taskid', models.CharField(max_length=32, unique=True, null=True)),
                ('season', models.CharField(max_length=16)),
                ('end_time', models.DateTimeField()),
                ('type', models.ForeignKey(to='lottery.Lotterytype')),
            ],
        ),
    ]
