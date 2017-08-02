# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-08-03 05:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('analyst', '0017_auto_20160519_1103'),
        ('mobileapp', '0010_livegift'),
    ]

    operations = [
        migrations.CreateModel(
            name='H5_article_fixtop',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_id', models.IntegerField(db_column=b'type')),
                ('article_id', models.IntegerField(db_column=b'articleid')),
                ('usable', models.BooleanField()),
                ('cdate', models.DateField()),
            ],
            options={
                'db_table': 'h5_article_fixtop',
            },
        ),
        migrations.CreateModel(
            name='H5_author_list',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usable', models.BooleanField()),
                ('order_id', models.IntegerField(db_column=b'orderid')),
                ('author', models.ForeignKey(db_column=b'authorid', on_delete=django.db.models.deletion.CASCADE, to='analyst.Analyst')),
            ],
            options={
                'db_table': 'h5_author_list',
            },
        ),
        migrations.RemoveField(
            model_name='livevedio',
            name='match',
        ),
        migrations.AddField(
            model_name='banner',
            name='target_url',
            field=models.CharField(blank=True, default=b'', max_length=100),
        ),
        migrations.AddField(
            model_name='livevedio',
            name='match_id',
            field=models.IntegerField(default=None),
        ),
        migrations.AddField(
            model_name='portal',
            name='target_url',
            field=models.CharField(blank=True, default=b'', max_length=100),
        ),
        migrations.AlterField(
            model_name='livevedio',
            name='cost',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='livevedio',
            name='location',
            field=models.SmallIntegerField(choices=[(1, '\u5317\u4eac'), (2, '\u4e0a\u6d77')], default=1),
        ),
    ]
