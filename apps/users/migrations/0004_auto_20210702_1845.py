# Generated by Django 3.2.3 on 2021-07-02 23:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20210702_0049'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='robohash_set',
            field=models.IntegerField(default=3),
        ),
        migrations.AddField(
            model_name='profile',
            name='user_location',
            field=models.CharField(default='Hell, Earth', max_length=100),
        ),
        migrations.AddField(
            model_name='profile',
            name='user_summary',
            field=models.CharField(default='I think my arm is on backward.', max_length=300),
        ),
    ]
