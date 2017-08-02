# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('lottery', '0001_initial'),
        ('analyst', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Analystlevel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('level_number', models.SmallIntegerField(unique=True)),
                ('name', models.CharField(max_length=16)),
            ],
        ),
        migrations.CreateModel(
            name='Priceplan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cost', models.SmallIntegerField()),
                ('analyst_level', models.ForeignKey(to='analyst.Analystlevel')),
                ('lottery_type', models.ForeignKey(to='lottery.Lotterytype')),
            ],
        ),
        migrations.AddField(
            model_name='analyst',
            name='address',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='analyst',
            name='date_added',
            field=models.DateTimeField(default=datetime.datetime(2015, 11, 19, 5, 31, 6, 66178, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='analyst',
            name='last_modified',
            field=models.DateTimeField(default=datetime.datetime(2015, 11, 19, 5, 31, 13, 379714, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='analyst',
            name='lottery_type',
            field=models.ForeignKey(default=1, to='lottery.Lotterytype'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='analyst',
            name='mobile',
            field=models.CharField(max_length=11, null=True),
        ),
        migrations.AddField(
            model_name='analyst',
            name='post_code',
            field=models.CharField(max_length=6, null=True),
        ),
        migrations.AddField(
            model_name='analyst',
            name='weichat',
            field=models.CharField(max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='analyst',
            name='level',
            field=models.ForeignKey(to='analyst.Analystlevel', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='priceplan',
            unique_together=set([('lottery_type', 'analyst_level')]),
        ),
    ]
