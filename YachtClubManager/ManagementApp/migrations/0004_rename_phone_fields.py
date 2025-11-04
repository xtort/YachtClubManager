# Generated manually for field renaming

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ManagementApp', '0003_clubuser_address1_clubuser_address2_clubuser_city_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='clubuser',
            old_name='phone_number',
            new_name='primary_phone_number',
        ),
        migrations.RenameField(
            model_name='clubuser',
            old_name='primary_phone',
            new_name='secondary_phone_number',
        ),
    ]

