# Generated by Django 3.2.3 on 2021-07-31 19:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0046_auto_20210731_1349'),
    ]

    operations = [
        migrations.AddField(
            model_name='playlist',
            name='auto_check_for_updates',
            field=models.BooleanField(default=False),
        ),
    ]
