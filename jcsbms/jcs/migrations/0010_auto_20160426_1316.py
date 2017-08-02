# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-26 05:16
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mobileapp', '0004_auto_20160328_1100'),
        ('analyst', '0015_analyst_analyst_group'),
        ('jcs', '0009_auto_20160406_1617'),
    ]

    operations = [
        migrations.CreateModel(
            name='BannedLettor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('analyst', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='analyst.Analyst')),
                ('auser', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='mobileapp.AppUser')),
            ],
        ),
        migrations.AlterField(
            model_name='letter',
            name='from_auser',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fromauser_letter', to='mobileapp.AppUser'),
        ),
        migrations.AlterField(
            model_name='letter',
            name='from_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fromuser_letter', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='letter',
            name='to_auser',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='toauser_letter', to='mobileapp.AppUser'),
        ),
        migrations.AlterField(
            model_name='letter',
            name='to_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='touser_letter', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='bannedlettor',
            unique_together=set([('auser', 'analyst')]),
        ),
    ]
