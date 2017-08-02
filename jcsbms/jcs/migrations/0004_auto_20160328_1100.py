# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('jcs', '0003_letter'),
    ]

    operations = [
        migrations.AlterField(
            model_name='letter',
            name='from_auser',
            field=models.ForeignKey(related_name='from_auser', to='mobileapp.AppUser', null=True),
        ),
        migrations.AlterField(
            model_name='letter',
            name='from_user',
            field=models.ForeignKey(related_name='from_user', to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='letter',
            name='to_auser',
            field=models.ForeignKey(related_name='to_auser', to='mobileapp.AppUser', null=True),
        ),
        migrations.AlterField(
            model_name='letter',
            name='to_user',
            field=models.ForeignKey(related_name='to_user', to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
