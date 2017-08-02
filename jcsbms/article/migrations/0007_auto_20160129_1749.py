# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0006_article_sign_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='chargeable',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='article',
            name='digest',
            field=models.CharField(max_length=300, null=True),
        ),
    ]
