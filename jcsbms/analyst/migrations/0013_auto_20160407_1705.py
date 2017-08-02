# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyst', '0012_analyst_answer_level'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analyst',
            name='answer_level',
            field=models.ForeignKey(blank=True, to='ask.AnswerLevel', null=True),
        ),
    ]
