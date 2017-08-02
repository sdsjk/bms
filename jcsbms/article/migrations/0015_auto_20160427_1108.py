# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-27 03:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mobileapp', '0007_portal'),
        ('article', '0014_delete_bannedword'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArticlePortalTags',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='article.Article')),
                ('portal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mobileapp.Portal')),
            ],
        ),
        migrations.AddField(
            model_name='article',
            name='portal_tags',
            field=models.ManyToManyField(through='article.ArticlePortalTags', to='mobileapp.Portal'),
        ),
        migrations.AlterUniqueTogether(
            name='articleportaltags',
            unique_together=set([('article', 'portal')]),
        ),
    ]