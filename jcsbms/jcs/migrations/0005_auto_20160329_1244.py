# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('jcs', '0004_auto_20160328_1100'),
    ]

    operations = [
        migrations.AlterField(
            model_name='letter',
            name='from_auser',
            field=models.ForeignKey(related_name='from_auser', blank=True, to='mobileapp.AppUser', null=True),
        ),
        migrations.AlterField(
            model_name='letter',
            name='from_user',
            field=models.ForeignKey(related_name='from_user', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='letter',
            name='to_auser',
            field=models.ForeignKey(related_name='to_auser', blank=True, to='mobileapp.AppUser', null=True),
        ),
        migrations.AlterField(
            model_name='letter',
            name='to_user',
            field=models.ForeignKey(related_name='to_user', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
