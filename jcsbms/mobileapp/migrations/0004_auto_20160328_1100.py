# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobileapp', '0003_moneychangehistory'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='moneychangehistory',
            table='money_change_history',
        ),
    ]
