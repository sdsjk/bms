# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyst', '0012_analyst_answer_level'),
        ('ask', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='question',
            old_name='user',
            new_name='from_user',
        ),
        migrations.AddField(
            model_name='question',
            name='to_analyst',
            field=models.ForeignKey(default=None, to='analyst.Analyst'),
            preserve_default=False,
        ),
    ]
