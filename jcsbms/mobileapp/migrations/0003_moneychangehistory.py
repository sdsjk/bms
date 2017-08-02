# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobileapp', '0002_charge_recharge'),
    ]

    operations = [
        migrations.CreateModel(
            name='MoneyChangeHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('origmoney', models.IntegerField()),
                ('operator', models.CharField(max_length=1)),
                ('changemoney', models.IntegerField()),
                ('leftmoney', models.IntegerField()),
                ('transctid', models.IntegerField()),
                ('cdate', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(db_column=b'userid', to='mobileapp.AppUser')),
            ],
            options={
                'db_table': 'MONEY_CHANGE_HISTORY',
                'managed': True,
            },
        ),
    ]
