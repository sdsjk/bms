# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ask', '0001_initial'),
        ('analyst', '0011_auto_20160219_1647'),
    ]

    operations = [
        migrations.AddField(
            model_name='analyst',
            name='answer_level',
            field=models.ForeignKey(to='ask.AnswerLevel', null=True),
        ),
    ]
