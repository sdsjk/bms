# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lottery', '0004_auto_20151125_1352'),
        ('article', '0003_auto_20151124_1454'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArticleLotteries',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='articlelottoes',
            name='article',
        ),
        migrations.RemoveField(
            model_name='articlelottoes',
            name='lotto',
        ),
        migrations.RemoveField(
            model_name='articlematchs',
            name='article',
        ),
        migrations.RemoveField(
            model_name='articlematchs',
            name='lotto',
        ),
        migrations.RemoveField(
            model_name='article',
            name='lottos',
        ),
        migrations.RemoveField(
            model_name='article',
            name='matchs',
        ),
        migrations.DeleteModel(
            name='ArticleLottoes',
        ),
        migrations.DeleteModel(
            name='ArticleMatchs',
        ),
        migrations.AddField(
            model_name='articlelotteries',
            name='article',
            field=models.ForeignKey(to='article.Article'),
        ),
        migrations.AddField(
            model_name='articlelotteries',
            name='lottery',
            field=models.ForeignKey(to='lottery.Lotteryentry'),
        ),
        migrations.AddField(
            model_name='article',
            name='lotteries',
            field=models.ManyToManyField(to='lottery.Lotteryentry', through='article.ArticleLotteries'),
        ),
    ]
