from django.shortcuts import render, redirect, get_object_or_404
from core.models import Artist, Task
from core.forms import ArtistForm, TaskForm
from django.http import HttpResponseRedirect
from django.urls import reverse

def artist_manager(request):
    """
    Main Artist Manager page:
    - shows all artists with their tasks
    - allows adding new artists
    - allows adding new tasks
    """
    artists = Artist.objects.prefetch_related("tasks")

    if request.method == "POST":
        if "add_artist" in request.POST:
            artist_form = ArtistForm(request.POST)
            task_form = TaskForm()  # keep empty for template
            if artist_form.is_valid():
                artist_form.save()
                return redirect("artist_manager")
        elif "add_task" in request.POST:
            task_form = TaskForm(request.POST)
            artist_form = ArtistForm()  # keep empty for template
            if task_form.is_valid():
                task_form.save()
                return redirect("artist_manager")
    else:
        artist_form = ArtistForm()
        task_form = TaskForm()

    return render(
        request,
        "core/artist_manager.html",  # matches core/templates/core/artist_manager.html
        {
            "artists": artists,
            "artist_form": artist_form,
            "task_form": task_form,
        },
    )

def update_task_status(request, task_id):
    """
    Updates the status of a Task and preserves open artists.
    """
    task = get_object_or_404(Task, pk=task_id)
    if request.method == "POST":
        task.status = request.POST.get("status")
        task.save()
        open_artists = request.POST.get("open_artists", "")
        return redirect(f"{reverse('artist_manager')}?open={open_artists}")
    return redirect("artist_manager")

def delete_task(request, task_id):
    """
    Deletes a Task and preserves open artists.
    """
    task = get_object_or_404(Task, pk=task_id)
    if request.method == "POST":
        open_artists = request.POST.get("open_artists", "")
        task.delete()
        return redirect(f"{reverse('artist_manager')}?open={open_artists}")
    return redirect("artist_manager")
