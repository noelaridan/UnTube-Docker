import datetime

import pytz
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from apps.main.models import Playlist, Tag
from django.contrib.auth.decorators import login_required  # redirects user to settings.LOGIN_URL
from allauth.socialaccount.models import SocialToken
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.template import Context, loader


# Create your views here.
@login_required
def home(request):
    user_profile = request.user.profile
    user_playlists = user_profile.playlists.filter(Q(is_in_db=True) & Q(num_of_accesses__gt=0)).order_by(
        "-num_of_accesses")
    watching = user_profile.playlists.filter(Q(marked_as="watching") & Q(is_in_db=True)).order_by("-num_of_accesses")
    recently_accessed_playlists = user_profile.playlists.filter(is_in_db=True).order_by("-updated_at")[:6]
    recently_added_playlists = user_profile.playlists.filter(is_in_db=True).order_by("-created_at")[:6]

    #### FOR NEWLY JOINED USERS ######
    channel_found = True
    if user_profile.show_import_page:
        """
        Logic:
        show_import_page is True by default. When a user logs in for the first time (infact anytime), google 
        redirects them to 'home' url. Since, show_import_page is True by default, the user is then redirected
        from 'home' to 'import_in_progress' url
        
        show_import_page is only set false in the import_in_progress.html page, i.e when user cancels YT import
        """
        # user_profile.show_import_page = False

        if user_profile.access_token.strip() == "" or user_profile.refresh_token.strip() == "":
            user_social_token = SocialToken.objects.get(account__user=request.user)
            user_profile.access_token = user_social_token.token
            user_profile.refresh_token = user_social_token.token_secret
            user_profile.expires_at = user_social_token.expires_at
            request.user.save()

        if user_profile.imported_yt_playlists:
            user_profile.show_import_page = False  # after user imports all their YT playlists no need to show_import_page again
            user_profile.save(update_fields=['show_import_page'])
            return render(request, "home.html", {"import_successful": True})

        return render(request, "import_in_progress.html")

        # if Playlist.objects.getUserYTChannelID(request.user) == -1:  # user channel not found
        #    channel_found = False
        # else:
        #   Playlist.objects.initPlaylist(request.user, None)  # get all playlists from user's YT channel
        #  return render(request, "home.html", {"import_successful": True})
    ##################################

    if request.method == "POST":
        print(request.POST)
        if Playlist.objects.initPlaylist(request.user, request.POST['playlist-id'].strip()) == -1:
            print("No such playlist found.")
            playlist = []
            videos = []
        else:
            playlist = user_profile.playlists.get(playlist_id__exact=request.POST['playlist-id'].strip())
            videos = playlist.videos.all()
    else:  # GET request
        videos = []
        playlist = []

        print("TESTING")

    return render(request, 'home.html', {"channel_found": channel_found,
                                         "playlist": playlist,
                                         "videos": videos,
                                         "user_playlists": user_playlists,
                                         "watching": watching,
                                         "recently_accessed_playlists": recently_accessed_playlists,
                                         "recently_added_playlists": recently_added_playlists})


@login_required
def view_video(request, playlist_id, video_id):
    video = request.user.profile.playlists.get(playlist_id=playlist_id).videos.get(video_id=video_id)
    print(video.name)
    return HttpResponse(loader.get_template("intercooler/video_details.html").render({"video": video}))


@login_required
def video_notes(request, playlist_id, video_id):
    video = request.user.profile.playlists.get(playlist_id=playlist_id).videos.get(video_id=video_id)

    if request.method == "POST":
        if 'video-notes-text-area' in request.POST:
            video.user_notes = request.POST['video-notes-text-area']
            video.save()
            return HttpResponse(loader.get_template("intercooler/messages.html").render(
                {"message_type": "success", "message_content": "Saved!"}))
    else:
        print("GET VIDEO NOTES")

    return HttpResponse(loader.get_template("intercooler/video_notes.html").render({"video": video,
                                                                                    "playlist_id": playlist_id}))


@login_required
def view_playlist(request, playlist_id):
    user_profile = request.user.profile

    # specific playlist requested
    if user_profile.playlists.filter(Q(playlist_id=playlist_id) & Q(is_in_db=True)).count() != 0:
        playlist = user_profile.playlists.get(playlist_id__exact=playlist_id)
        playlist.num_of_accesses += 1
        playlist.save()
    else:
        messages.error(request, "No such playlist found!")
        return redirect('home')

    if playlist.has_new_updates:
        recently_updated_videos = playlist.videos.filter(video_details_modified=True)

        for video in recently_updated_videos:
            if video.video_details_modified_at + datetime.timedelta(hours=12) < datetime.datetime.now(
                    pytz.utc):  # expired
                video.video_details_modified = False
                video.save()

        if recently_updated_videos.count() == 0:
            playlist.has_new_updates = False
            playlist.save()

    videos = playlist.videos.order_by("video_position")

    user_created_tags = Tag.objects.filter(created_by=request.user)
    playlist_tags = playlist.tags.all()

    unused_tags = user_created_tags.difference(playlist_tags)

    return render(request, 'view_playlist.html', {"playlist": playlist,
                                                  "playlist_tags": playlist_tags,
                                                  "unused_tags": unused_tags,
                                                  "videos": videos})


@login_required
def all_playlists(request, playlist_type):
    """
    Possible playlist types for marked_as attribute: (saved in database like this)
    "none", "watching", "plan-to-watch"
    """
    playlist_type = playlist_type.lower()

    if playlist_type == "" or playlist_type == "all":
        playlists = request.user.profile.playlists.all().filter(is_in_db=True)
        playlist_type_display = "All Playlists"
    elif playlist_type == "user-owned":  # YT playlists owned by user
        playlists = request.user.profile.playlists.all().filter(Q(is_user_owned=True) & Q(is_in_db=True))
        playlist_type_display = "Your YouTube Playlists"
    elif playlist_type == "imported":  # YT playlists (public) owned by others
        playlists = request.user.profile.playlists.all().filter(Q(is_user_owned=False) & Q(is_in_db=True))
        playlist_type_display = "Imported playlists"
    elif playlist_type == "favorites":  # YT playlists (public) owned by others
        playlists = request.user.profile.playlists.all().filter(Q(is_favorite=True) & Q(is_in_db=True))
        playlist_type_display = "Favorites"
    elif playlist_type.lower() in ["watching", "plan-to-watch"]:
        playlists = request.user.profile.playlists.filter(Q(marked_as=playlist_type.lower()) & Q(is_in_db=True))
        playlist_type_display = playlist_type.lower().replace("-", " ")
    elif playlist_type.lower() == "home":  # displays cards of all playlist types
        return render(request, 'playlists_home.html')
    else:
        return redirect('home')

    return render(request, 'all_playlists.html', {"playlists": playlists,
                                                  "playlist_type": playlist_type,
                                                  "playlist_type_display": playlist_type_display})


@login_required
def order_playlist_by(request, playlist_id, order_by):
    playlist = request.user.profile.playlists.get(Q(playlist_id=playlist_id) & Q(is_in_db=True))

    display_text = "Nothing in this playlist! Add something!"  # what to display when requested order/filter has no videws
    videos_details = ""

    if order_by == "all":
        videos = playlist.videos.order_by("video_position")
    elif order_by == "favorites":
        videos = playlist.videos.filter(is_favorite=True).order_by("video_position")
        videos_details = "Sorted by Favorites"
        display_text = "No favorites yet!"
    elif order_by == "popularity":
        videos_details = "Sorted by Popularity"
        videos = playlist.videos.order_by("-like_count")
    elif order_by == "date-published":
        videos_details = "Sorted by Date Published"
        videos = playlist.videos.order_by("-published_at")
    elif order_by == "views":
        videos_details = "Sorted by View Count"
        videos = playlist.videos.order_by("-view_count")
    elif order_by == "has-cc":
        videos_details = "Filtered by Has CC"
        videos = playlist.videos.filter(has_cc=True).order_by("video_position")
        display_text = "No videos in this playlist have CC :("
    elif order_by == "duration":
        videos_details = "Sorted by Video Duration"
        videos = playlist.videos.order_by("-duration_in_seconds")
    elif order_by == 'new-updates':
        videos = []
        videos_details = "Sorted by New Updates"
        display_text = "No new updates! Note that deleted videos will not show up here."
        if playlist.has_new_updates:
            recently_updated_videos = playlist.videos.filter(video_details_modified=True)

            for video in recently_updated_videos:
                if video.video_details_modified_at + datetime.timedelta(hours=12) < datetime.datetime.now(
                        pytz.utc):  # expired
                    video.video_details_modified = False
                    video.save()

            if recently_updated_videos.count() == 0:
                playlist.has_new_updates = False
                playlist.save()
            else:
                videos = recently_updated_videos.order_by("video_position")
    elif order_by == 'unavailable-videos':
        videos = playlist.videos.filter(Q(is_unavailable_on_yt=True) & Q(was_deleted_on_yt=True))
        videos_details = "Sorted by Unavailable Videos"
        display_text = "None of the videos in this playlist have gone unavailable... yet."
    else:
        return redirect('home')

    return HttpResponse(loader.get_template("intercooler/videos.html").render({"playlist": playlist,
                                                                               "videos": videos,
                                                                               "videos_details": videos_details,
                                                                               "display_text": display_text}))


@login_required
def order_playlists_by(request, playlist_type, order_by):
    if playlist_type == "" or playlist_type.lower() == "all":
        playlists = request.user.profile.playlists.all()
        playlist_type_display = "All Playlists"
    elif playlist_type.lower() == "favorites":
        playlists = request.user.profile.playlists.filter(Q(is_favorite=True) & Q(is_in_db=True))
        playlist_type_display = "Favorites"
    elif playlist_type.lower() in ["watching", "plan-to-watch"]:
        playlists = request.user.profile.playlists.filter(Q(marked_as=playlist_type.lower()) & Q(is_in_db=True))
        playlist_type_display = "Watching"
    else:
        return redirect('home')

    if order_by == 'recently-accessed':
        playlists = playlists.order_by("-updated_at")
    elif order_by == 'playlist-duration-in-seconds':
        playlists = playlists.order_by("-playlist_duration_in_seconds")
    elif order_by == 'video-count':
        playlists = playlists.order_by("-video_count")

    return HttpResponse(loader.get_template("intercooler/playlists.html")
                        .render({"playlists": playlists,
                                 "playlist_type_display": playlist_type_display,
                                 "playlist_type": playlist_type}))


@login_required
def mark_playlist_as(request, playlist_id, mark_as):
    playlist = request.user.profile.playlists.get(playlist_id=playlist_id)

    marked_as_response = ""

    if mark_as in ["watching", "on-hold", "plan-to-watch"]:
        playlist.marked_as = mark_as
        playlist.save()
        marked_as_response = f'<span class="badge bg-success text-white" >{mark_as.replace("-", " ")}</span>'
    elif mark_as == "none":
        playlist.marked_as = mark_as
        playlist.save()
    elif mark_as == "favorite":
        if playlist.is_favorite:
            playlist.is_favorite = False
            playlist.save()
            return HttpResponse('<i class="far fa-star"></i>')
        else:
            playlist.is_favorite = True
            playlist.save()
            return HttpResponse('<i class="fas fa-star"></i>')
    else:
        return render('home')

    return HttpResponse(marked_as_response)


@login_required
def playlists_home(request):
    return render(request, 'playlists_home.html')


@login_required
@require_POST
def delete_videos(request, playlist_id, command):
    video_ids = request.POST.getlist("video-id", default=[])

    if command == "confirm":
        print(video_ids)
        num_vids = len(video_ids)
        extra_text = " "
        if num_vids == 0:
            return HttpResponse("<h5>Select some videos first!</h5>")
        elif num_vids == request.user.profile.playlists.get(playlist_id=playlist_id).videos.all().count():
            delete_text = "ALL VIDEOS"
            extra_text = " This will not delete the playlist itself, will only make the playlist empty. "
        else:
            delete_text = f"{num_vids} videos"
        return HttpResponse(
            f"<h5>Are you sure you want to delete {delete_text} from your YouTube playlist?{extra_text}This cannot be undone.</h5>")
    elif command == "confirmed":
        print(video_ids)
        return HttpResponse(
            f'<div class="spinner-border text-light" role="status" hx-post="/from/{playlist_id}/delete-videos/start" hx-trigger="load" hx-swap="outerHTML"></div>')
    elif command == "start":
        Playlist.objects.deletePlaylistItems(request.user, playlist_id, video_ids)
        # playlist = request.user.profile.playlists.get(playlist_id=playlist_id)
        # playlist.has_playlist_changed = True
        # playlist.save(update_fields=['has_playlist_changed'])
        return HttpResponse(f"""
        <div hx-get="/playlist/{playlist_id}/update/checkforupdates" hx-trigger="load delay:4s" hx-target="#checkforupdates" class="sticky-top" style="top: 0.5rem;">
Done! Playlist on UnTube will update in 3s...
        </div>
        """)


@login_required
@require_POST
def search_playlists(request, playlist_type):
    print(request.POST)  # prints <QueryDict: {'search': ['aa']}>

    search_query = request.POST["search"]

    if playlist_type == "all":
        try:
            playlists = request.user.profile.playlists.all().filter(Q(name__startswith=search_query) & Q(is_in_db=True))
        except:
            playlists = request.user.profile.playlists.all()
        playlist_type_display = "All Playlists"
    elif playlist_type == "user-owned":  # YT playlists owned by user
        try:
            playlists = request.user.profile.playlists.filter(
                Q(name__startswith=search_query) & Q(is_user_owned=True) & Q(is_in_db=True))
        except:
            playlists = request.user.profile.playlists.filter(Q(is_user_owned=True) & Q(is_in_db=True))
        playlist_type_display = "Your YouTube Playlists"
    elif playlist_type == "imported":  # YT playlists (public) owned by others
        try:
            playlists = request.user.profile.playlists.filter(
                Q(name__startswith=search_query) & Q(is_user_owned=False) & Q(is_in_db=True))
        except:
            playlists = request.user.profile.playlists.filter(Q(is_user_owned=True) & Q(is_in_db=True))
        playlist_type_display = "Imported Playlists"
    elif playlist_type == "favorites":  # YT playlists (public) owned by others
        try:
            playlists = request.user.profile.playlists.filter(
                Q(name__startswith=search_query) & Q(is_favorite=True) & Q(is_in_db=True))
        except:
            playlists = request.user.profile.playlists.filter(Q(is_favorite=True) & Q(is_in_db=True))
        playlist_type_display = "Your Favorites"
    elif playlist_type in ["watching", "plan-to-watch"]:
        try:
            playlists = request.user.profile.playlists.filter(
                Q(name__startswith=search_query) & Q(marked_as=playlist_type) & Q(is_in_db=True))
        except:
            playlists = request.user.profile.playlists.all().filter(Q(marked_as=playlist_type) & Q(is_in_db=True))
        playlist_type_display = playlist_type.replace("-", " ")

    return HttpResponse(loader.get_template("intercooler/playlists.html")
                        .render({"playlists": playlists,
                                 "playlist_type_display": playlist_type_display,
                                 "playlist_type": playlist_type,
                                 "search_query": search_query}))


#### MANAGE VIDEOS #####
def mark_video_favortie(request, playlist_id, video_id):
    video = request.user.profile.playlists.get(playlist_id=playlist_id).videos.get(video_id=video_id)

    if video.is_favorite:
        video.is_favorite = False
        video.save()
        return HttpResponse('<i class="far fa-heart"></i>')
    else:
        video.is_favorite = True
        video.save()
        return HttpResponse('<i class="fas fa-heart"></i>')


###########
@login_required
def search(request):
    if request.method == "GET":
        return render(request, 'search_untube_page.html')
    else:
        return render('home')


@login_required
@require_POST
def search_UnTube(request):
    print(request.POST)

    search_query = request.POST["search"]

    all_playlists = request.user.profile.playlists.filter(is_in_db=True)
    videos = []
    starts_with = False
    contains = False

    if request.POST['search-settings'] == 'starts-with':
        playlists = request.user.profile.playlists.filter(
            Q(name__startswith=search_query) & Q(is_in_db=True)) if search_query != "" else []

        if search_query != "":
            for playlist in all_playlists:
                pl_videos = playlist.videos.filter(name__startswith=search_query)

                if pl_videos.count() != 0:
                    for v in pl_videos.all():
                        videos.append(v)

        starts_with = True
    else:
        playlists = request.user.profile.playlists.filter(
            Q(name__contains=search_query) & Q(is_in_db=True)) if search_query != "" else []

        if search_query != "":
            for playlist in all_playlists:
                pl_videos = playlist.videos.filter(name__contains=search_query)

                if pl_videos.count() != 0:
                    for v in pl_videos.all():
                        videos.append(v)

        contains = True
    return HttpResponse(loader.get_template("intercooler/search_untube.html")
                        .render({"playlists": playlists,
                                 "videos": videos,
                                 "videos_count": len(videos),
                                 "search_query": search_query,
                                 "starts_with": starts_with,
                                 "contains": contains}))


@login_required
def manage_playlists(request):
    return render(request, "manage_playlists.html")


@login_required
def manage_view_page(request, page):
    if page == "import":
        return render(request, "manage_playlists_import.html",
                      {"manage_playlists_import_textarea": request.user.profile.manage_playlists_import_textarea})
    elif page == "create":
        return render(request, "manage_playlists_create.html")
    else:
        return HttpResponse('Working on this!')


@login_required
@require_POST
def manage_save(request, what):
    if what == "manage_playlists_import_textarea":
        request.user.profile.manage_playlists_import_textarea = request.POST["import-playlist-textarea"]
        request.user.save()

    return HttpResponse("")


@login_required
@require_POST
def manage_import_playlists(request):
    playlist_links = request.POST["import-playlist-textarea"].replace(",", "").split("\n")

    num_playlists_already_in_db = 0
    num_playlists_initialized_in_db = 0
    num_playlists_not_found = 0
    new_playlists = []
    old_playlists = []
    not_found_playlists = []

    done = []
    for playlist_link in playlist_links:
        if playlist_link.strip() != "" and playlist_link.strip() not in done:
            pl_id = Playlist.objects.getPlaylistId(playlist_link.strip())
            if pl_id is None:
                num_playlists_not_found += 1
                continue
            status = Playlist.objects.initPlaylist(request.user, pl_id)
            if status == -1 or status == -2:
                print("\nNo such playlist found:", pl_id)
                num_playlists_not_found += 1
                not_found_playlists.append(playlist_link)
            elif status == -3:
                num_playlists_already_in_db += 1
                playlist = request.user.profile.playlists.get(playlist_id__exact=pl_id)
                old_playlists.append(playlist)
            else:
                print(status)
                playlist = request.user.profile.playlists.get(playlist_id__exact=pl_id)
                new_playlists.append(playlist)
                num_playlists_initialized_in_db += 1
            done.append(playlist_link.strip())

    request.user.profile.manage_playlists_import_textarea = ""
    request.user.save()

    return HttpResponse(loader.get_template("intercooler/manage_playlists_import_results.html")
        .render(
        {"new_playlists": new_playlists,
         "old_playlists": old_playlists,
         "not_found_playlists": not_found_playlists,
         "num_playlists_already_in_db": num_playlists_already_in_db,
         "num_playlists_initialized_in_db": num_playlists_initialized_in_db,
         "num_playlists_not_found": num_playlists_not_found
         }))


@login_required
@require_POST
def manage_create_playlist(request):
    print(request.POST)
    return HttpResponse("")


@login_required
def load_more_videos(request, playlist_id, page):
    playlist = request.user.profile.playlists.get(playlist_id=playlist_id)
    videos = playlist.videos.order_by("video_position")[50 * page:]

    return HttpResponse(loader.get_template("intercooler/videos.html")
        .render(
        {
            "playlist": playlist,
            "videos": videos,
            "page": page + 1}))


@login_required
@require_POST
def update_playlist_settings(request, playlist_id):
    message_type = "success"
    message_content = "Saved!"

    if "user_label" in request.POST:
        playlist = request.user.profile.playlists.get(playlist_id=playlist_id)
        playlist.user_label = request.POST["user_label"]
        playlist.save(update_fields=['user_label'])

        return HttpResponse(loader.get_template("intercooler/messages.html")
            .render(
            {"message_type": message_type,
             "message_content": message_content}))

    details = {
        "title": request.POST['playlistTitle'],
        "description": request.POST['playlistDesc'],
        "privacyStatus": True if request.POST['playlistPrivacy'] == "Private" else False
    }

    status = Playlist.objects.updatePlaylistDetails(request.user, playlist_id, details)
    if status == -1:
        message_type = "error"
        message_content = "Could not save :("

    return HttpResponse(loader.get_template("intercooler/messages.html")
        .render(
        {"message_type": message_type,
         "message_content": message_content}))


@login_required
def update_playlist(request, playlist_id, type):
    playlist = request.user.profile.playlists.get(playlist_id=playlist_id)

    if type == "checkforupdates":
        print("Checking if playlist changed...")
        result = Playlist.objects.checkIfPlaylistChangedOnYT(request.user, playlist_id)

        if result[0] == 1:  # full scan was done (full scan is done for a playlist if a week has passed)
            deleted_videos, unavailable_videos, added_videos = result[1:]

            print("CHANGES", deleted_videos, unavailable_videos, added_videos)

            # playlist_changed_text = ["The following modifications happened to this playlist on YouTube:"]
            if deleted_videos != 0 or unavailable_videos != 0 or added_videos != 0:
                pass
                # if added_videos > 0:
                #    playlist_changed_text.append(f"{added_videos} new video(s) were added")
                # if deleted_videos > 0:
                #    playlist_changed_text.append(f"{deleted_videos} video(s) were deleted")
                # if unavailable_videos > 0:
                #    playlist_changed_text.append(f"{unavailable_videos} video(s) went private/unavailable")

                # playlist.playlist_changed_text = "\n".join(playlist_changed_text)
                # playlist.has_playlist_changed = True
                # playlist.save()
            else:  # no updates found
                return HttpResponse("""
                <div id="checkforupdates" class="sticky-top" style="top: 0.5em;">
                <div class="alert alert-success alert-dismissible fade show visually-hidden" role="alert">
                    No new updates!
                </div>
                <br>
                </div>
                """)
        elif result[0] == -1:  # playlist changed
            print("!!!Playlist changed")

            # current_playlist_vid_count = playlist.video_count
            # new_playlist_vid_count = result[1]

            # print(current_playlist_vid_count)
            # print(new_playlist_vid_count)

            # playlist.has_playlist_changed = True
            # playlist.save()
            # print(playlist.playlist_changed_text)
        else:  # no updates found
            return HttpResponse("""
            <div id="checkforupdates" class="sticky-top" style="top: 0.5em;">
            <div class="alert alert-success alert-dismissible fade show visually-hidden sticky-top" role="alert" style="top: 0.5em;">
                No new updates!
            </div>
            <br>
            </div>
            """)

        return HttpResponse(f"""
        <div hx-get="/playlist/{playlist_id}/update/auto" hx-trigger="load" hx-target="this" class="sticky-top" style="top: 0.5em;">
            
            <div class="alert alert-success alert-dismissible fade show" role="alert">
            <div class="d-flex justify-content-center" id="loading-sign">
                <img src="/static/svg-loaders/circles.svg" width="40" height="40">
                <h5 class="mt-2 ms-2">Changes detected on YouTube, updating playlist '{playlist.name}'...</h5>
            </div>
            </div>
        </div>
        """)

    if type == "manual":
        print("MANUAL")
        return HttpResponse(
            f"""<div hx-get="/playlist/{playlist_id}/update/auto" hx-trigger="load" hx-swap="outerHTML">
                    <div class="d-flex justify-content-center mt-4 mb-3" id="loading-sign">
                        <img src="/static/svg-loaders/circles.svg" width="40" height="40">
                        <h5 class="mt-2 ms-2">Refreshing playlist '{playlist.name}', please wait!</h5>
                    </div>
                </div>""")

    print("Attempting to update playlist")
    status, deleted_video_ids, unavailable_videos, added_videos = Playlist.objects.updatePlaylist(request.user,
                                                                                                  playlist_id)

    playlist = request.user.profile.playlists.get(playlist_id=playlist_id)

    if status == -1:
        playlist_name = playlist.name
        playlist.delete()
        return HttpResponse(
            f"""
                <div class="d-flex justify-content-center mt-4 mb-3" id="loading-sign">
                    <h5 class="mt-2 ms-2">Looks like the playlist '{playlist_name}' was deleted on YouTube. It has been removed from UnTube as well.</h5>
                </div>
            """)

    print("Updated playlist")
    playlist_changed_text = []

    if len(added_videos) != 0:
        playlist_changed_text.append(f"{len(added_videos)} added")
        for video in added_videos:
            playlist_changed_text.append(f"--> {video.name}")

        # if len(added_videos) > 3:
        #    playlist_changed_text.append(f"+ {len(added_videos) - 3} more")

    if len(unavailable_videos) != 0:
        if len(playlist_changed_text) == 0:
            playlist_changed_text.append(f"{len(unavailable_videos)} went unavailable")
        else:
            playlist_changed_text.append(f"\n{len(unavailable_videos)} went unavailable")
        for video in unavailable_videos:
            playlist_changed_text.append(f"--> {video.name}")
    if len(deleted_video_ids) != 0:
        if len(playlist_changed_text) == 0:
            playlist_changed_text.append(f"{len(deleted_video_ids)} deleted")
        else:
            playlist_changed_text.append(f"\n{len(deleted_video_ids)} deleted")

        for video_id in deleted_video_ids:
            video = playlist.videos.get(video_id=video_id)
            playlist_changed_text.append(f"--> {video.name}")
            video.delete()

    if len(playlist_changed_text) == 0:
        playlist_changed_text = ["Successfully refreshed playlist! No new changes found!"]

    # return HttpResponse
    return HttpResponse(loader.get_template("intercooler/playlist_updates.html")
        .render(
        {"playlist_changed_text": "\n".join(playlist_changed_text),
         "playlist_id": playlist_id}))

@login_required
def view_playlist_settings(request, playlist_id):
    playlist = request.user.profile.playlists.get(playlist_id=playlist_id)

    return render(request, 'view_playlist_settings.html', {"playlist": playlist})


def get_playlist_tags(request, playlist_id):
    playlist = request.user.profile.playlists.get(playlist_id=playlist_id)
    playlist_tags = playlist.tags.all()

    return HttpResponse(loader.get_template("intercooler/playlist_tags.html")
        .render(
        {"playlist_id": playlist_id,
            "playlist_tags": playlist_tags}))


def get_unused_playlist_tags(request, playlist_id):
    playlist = request.user.profile.playlists.get(playlist_id=playlist_id)

    user_created_tags = Tag.objects.filter(created_by=request.user)
    playlist_tags = playlist.tags.all()

    unused_tags = user_created_tags.difference(playlist_tags)

    return HttpResponse(loader.get_template("intercooler/playlist_tags_unused.html")
        .render(
        {"unused_tags": unused_tags}))

@login_required
@require_POST
def create_playlist_tag(request, playlist_id):
    tag_name = request.POST["createTagField"]

    if tag_name == 'Pick from existing unused tags':
        return HttpResponse("Can't use that! Try again >_<")

    playlist = request.user.profile.playlists.get(playlist_id=playlist_id)

    user_created_tags = Tag.objects.filter(created_by=request.user)
    if user_created_tags.filter(name__iexact=tag_name).count() == 0:  # no tag found, so create it
        tag = Tag(name=tag_name, created_by=request.user)
        tag.save()

        # add it to playlist
        playlist.tags.add(tag)

    else:
        return HttpResponse("""
                            Already created. Try Again >w<
                    """)

    #playlist_tags = playlist.tags.all()

    #unused_tags = user_created_tags.difference(playlist_tags)

    return HttpResponse(f"""
            Created and Added!
              <span class="visually-hidden" hx-get="/playlist/{playlist_id}/get-tags" hx-trigger="load" hx-target="#playlist-tags"></span>
    """)


@login_required
@require_POST
def add_playlist_tag(request, playlist_id):

    tag_name = request.POST["playlistTag"]

    if tag_name == 'Pick from existing unused tags':
        return HttpResponse("Pick something! >w<")

    playlist = request.user.profile.playlists.get(playlist_id=playlist_id)

    playlist_tags = playlist.tags.all()
    if playlist_tags.filter(name__iexact=tag_name).count() == 0:  # tag not on this playlist, so add it
        tag = Tag.objects.filter(Q(created_by=request.user) & Q(name__iexact=tag_name)).first()

        # add it to playlist
        playlist.tags.add(tag)
    else:
        return HttpResponse("Already Added >w<")

    return HttpResponse(f"""
                Added!
                  <span class="visually-hidden" hx-get="/playlist/{playlist_id}/get-tags" hx-trigger="load" hx-target="#playlist-tags"></span>
        """)


@login_required
@require_POST
def remove_playlist_tag(request, playlist_id, tag_name):
    playlist = request.user.profile.playlists.get(playlist_id=playlist_id)

    playlist_tags = playlist.tags.all()
    if playlist_tags.filter(name__iexact=tag_name).count() != 0:  # tag on this playlist, remove it it
        tag = Tag.objects.filter(Q(created_by=request.user) & Q(name__iexact=tag_name)).first()

        print("Removed tag", tag_name)
        # remove it from the playlist
        playlist.tags.remove(tag)
    else:
        return HttpResponse("Whoops >w<")

    return HttpResponse("")

