# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('mobileapp', '0003_moneychangehistory'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('jcs', '0002_bulletin'),
    ]

    operations = [
        migrations.CreateModel(
            name='Letter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('unread', models.BooleanField(default=True)),
                ('content', models.CharField(max_length=320)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('from_auser', models.ForeignKey(related_name='from_auser', to='mobileapp.AppUser')),
                ('from_user', models.ForeignKey(related_name='from_user', to=settings.AUTH_USER_MODEL)),
                ('to_auser', models.ForeignKey(related_name='to_auser', to='mobileapp.AppUser')),
                ('to_user', models.ForeignKey(related_name='to_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
