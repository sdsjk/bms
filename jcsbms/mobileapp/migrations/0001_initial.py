# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.utils.timezone import utc
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('analyst', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppUser',
            fields=[
                ('userid', models.IntegerField(serialize=False, primary_key=True)),
                ('phonenumber', models.CharField(db_index=True, max_length=13, unique=True)),
                ('password', models.CharField(max_length=64)),
                ('nickname', models.CharField(max_length=20, null=True)),
                ('age', models.SmallIntegerField(null=True)),
                ('securitykey', models.CharField(max_length=32, null=True)),
                ('payinfo', models.SmallIntegerField()),
                ('money', models.IntegerField()),
                ('picpath', models.CharField(max_length=1024)),
                ('isactive', models.BooleanField(default=True)),
                ('cdate', models.DateTimeField(auto_now_add=True)),
                ('deviceno', models.CharField(max_length=100)),
                ('goldcoin', models.IntegerField()),
                ('inviter', models.ForeignKey(db_column=b'inviteid', to='analyst.Analyst', null=True)),
                ('channel', models.IntegerField(db_column=b'channelid', null=True)),
                ('os', models.CharField(max_length=16)),
                ('udate', models.DateTimeField()),
                ('usertype', models.SmallIntegerField()),
                ('version', models.CharField(max_length=16)),
                ('channelname', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'users',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Follow',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('author',models.ForeignKey(db_column=b'authorid', null=True, on_delete=django.db.models.deletion.CASCADE, to='analyst.Analyst')),
                ('user', models.ForeignKey(db_column=b'userid', null=True, on_delete=django.db.models.deletion.CASCADE, to='mobileapp.AppUser')),
            ],
            options={
                'db_table': 'follow',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('price', models.IntegerField()),
                ('author', models.ForeignKey(db_column=b'authorid',to='analyst.Analyst')),
                ('cdate', models.DateTimeField(auto_now_add=True)),
                ('paymentid', models.IntegerField()),
                ('paytype', models.SmallIntegerField()),
                ('purchasetype', models.SmallIntegerField()),
                ('status',models.SmallIntegerField()),
                ('target', models.IntegerField(db_column=b'targetid')),
                ('user', models.ForeignKey(db_column=b'userid', to='mobileapp.AppUser')),
            ],
            options={
                'db_table': 'purchase',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Period',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('startdate', models.DateTimeField()),
                ('enddate', models.DateTimeField()),
            ],
            options={
                'db_table': 'period',
                'managed': True,
            },
        ),
    ]
