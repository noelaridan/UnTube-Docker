# Generated by Django 3.2.3 on 2021-07-09 23:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_playlist_tags'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlaylistItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('playlist_item_id', models.CharField(max_length=100)),
                ('video_position', models.IntegerField(blank=True)),
                ('user_notes', models.CharField(default='', max_length=420)),
                ('is_duplicate', models.BooleanField(default=False)),
                ('is_marked_as_watched', models.BooleanField(blank=True, default=False)),
                ('is_favorite', models.BooleanField(blank=True, default=False)),
                ('num_of_accesses', models.CharField(default='0', max_length=69)),
                ('user_label', models.CharField(default='', max_length=100)),
                ('video_details_modified', models.BooleanField(default=False)),
                ('video_details_modified_at', models.DateTimeField(auto_now_add=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('playlist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='playlist_items', to='main.playlist')),
                ('video', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='playlists', to='main.video')),
            ],
        ),
    ]
