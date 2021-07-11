# Generated by Django 3.2.3 on 2021-07-06 02:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_remove_playlist_playlist_updates_text'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlaylistItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('playlist_item_id', models.CharField(max_length=100)),
                ('playlist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='playlist_items', to='main.playlist')),
            ],
        ),
        migrations.AddField(
            model_name='video',
            name='playlist_items',
            field=models.ManyToManyField(related_name='playlists', to='main.PlaylistItem'),
        ),
    ]
