from django.db.models import Count, Q
from django.http import JsonResponse


def channel_videos_distribution(request, playlist_id):
    labels = []
    data = []

    playlist_items = request.user.playlists.get(playlist_id=playlist_id).playlist_items.all()

    queryset = playlist_items.filter(Q(video__is_unavailable_on_yt=False) & Q(video__was_deleted_on_yt=False)).values(
        'video__channel_name').annotate(channel_videos_count=Count('video_position')).order_by(
        '-channel_videos_count')
    for entry in queryset:
        labels.append(entry['video__channel_name'])
        data.append(entry['channel_videos_count'])

    return JsonResponse(data={
        'labels': labels,
        'data': data,
    })


def overall_playlists_distribution(request):
    labels = []
    data = []

    user_playlists = request.user.playlists.filter(is_in_db=True)
    total_num_playlists = user_playlists.count()
    user_playlists = user_playlists.filter(num_of_accesses__gt=0).order_by(
        "-num_of_accesses")

    statistics = {
        "public": 0,
        "private": 0,
        "favorites": 0,
        "watching": 0,
        "imported": 0,
        "youtube mixes": 0
    }

    if total_num_playlists != 0:
        statistics["public"] = user_playlists.filter(is_private_on_yt=False).count()
        statistics["private"] = user_playlists.filter(is_private_on_yt=True).count()
        statistics["favorites"] = user_playlists.filter(is_favorite=True).count()
        statistics["watching"] = user_playlists.filter(marked_as="watching").count()
        statistics["imported"] = user_playlists.filter(is_user_owned=False).count()
        statistics["youtube mixes"] = user_playlists.filter(is_yt_mix=True).count()


    for key, value in statistics.items():
        labels.append(key)
        data.append(value)

    return JsonResponse(data={
        'labels': labels,
        'data': data,
    })
