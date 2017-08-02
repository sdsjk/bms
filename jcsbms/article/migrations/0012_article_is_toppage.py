# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0011_article_end_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='is_toppage',
            field=models.BooleanField(default=False),
        ),
    ]
