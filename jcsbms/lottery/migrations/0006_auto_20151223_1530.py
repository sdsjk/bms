# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lottery', '0005_match_mattch_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='match',
            old_name='mattch_id',
            new_name='match_id',
        ),
    ]
