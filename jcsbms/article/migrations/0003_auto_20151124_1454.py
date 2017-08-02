# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lottery', '0003_lotto'),
        ('article', '0002_auto_20151123_1751'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArticleLottoes',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('article', models.ForeignKey(to='article.Article')),
                ('lotto', models.ForeignKey(to='lottery.Lotto')),
            ],
        ),
        migrations.CreateModel(
            name='ArticleMatchs',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('article', models.ForeignKey(to='article.Article')),
                ('lotto', models.ForeignKey(to='lottery.Match')),
            ],
        ),
        migrations.AddField(
            model_name='article',
            name='lottos',
            field=models.ManyToManyField(to='lottery.Lotto', through='article.ArticleLottoes'),
        ),
        migrations.AddField(
            model_name='article',
            name='matchs',
            field=models.ManyToManyField(to='lottery.Match', through='article.ArticleMatchs'),
        ),
    ]
