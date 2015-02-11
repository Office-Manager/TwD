# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rango', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='page',
            old_name='urls',
            new_name='url',
        ),
    ]
