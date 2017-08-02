# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jcs', '0006_letter_to_author'),
    ]

    operations = [
        migrations.RenameField(
            model_name='letter',
            old_name='to_author',
            new_name='to_analyst',
        ),
    ]
