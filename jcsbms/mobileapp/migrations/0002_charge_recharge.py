# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mobileapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Charge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('money', models.IntegerField()),
                ('gold', models.IntegerField(db_column=b'goldcoin')),
                ('bank', models.CharField(max_length=48)),
                ('type', models.SmallIntegerField()),
                ('status', models.SmallIntegerField()),
                ('cdate', models.DateTimeField(auto_now_add=True)),
                ('user',models.ForeignKey(db_column=b'userid', on_delete=django.db.models.deletion.CASCADE, to='mobileapp.AppUser')),
            ],
            options={
                'db_table': 'charge',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Recharge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('gold_number', models.SmallIntegerField()),
                ('cost', models.SmallIntegerField()),
            ],
        ),
    ]
