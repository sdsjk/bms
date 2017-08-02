# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Analyst',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('analyst_type', models.SmallIntegerField()),
                ('nick_name', models.CharField(unique=True, max_length=16)),
                ('brief', models.CharField(max_length=500)),
                ('real_name', models.CharField(max_length=4, null=True)),
                ('id_number', models.CharField(max_length=20, null=True)),
                ('bank_branch', models.CharField(max_length=200, null=True)),
                ('card_number', models.CharField(max_length=32, null=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
