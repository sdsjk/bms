# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lottery', '0003_lotto'),
    ]

    operations = [
        migrations.CreateModel(
            name='Lotteryentry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('taskid', models.CharField(max_length=32, unique=True, null=True)),
                ('type', models.ForeignKey(to='lottery.Lotterytype')),
            ],
        ),
        migrations.RemoveField(
            model_name='lotto',
            name='taskid',
        ),
        migrations.RemoveField(
            model_name='lotto',
            name='type',
        ),
        migrations.RemoveField(
            model_name='match',
            name='taskid',
        ),
        migrations.RemoveField(
            model_name='match',
            name='type',
        ),
        migrations.AddField(
            model_name='lotto',
            name='lottery_entry',
            field=models.OneToOneField(default=1, to='lottery.Lotteryentry'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='match',
            name='lottery_entry',
            field=models.OneToOneField(default=1, to='lottery.Lotteryentry'),
            preserve_default=False,
        ),
    ]
