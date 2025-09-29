from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404

from core.forms import ShotForm
from core.models import Project, Publish, Sequence, Shot, Task


# Shot views
# List shots with project and sequence filtering
def add_shot(request,pk=None):
    instance = Shot.objects.get(pk=pk) if pk else None
    if request.method == 'POST':
        form = ShotForm(request.POST, request.FILES,instance=instance)
        if form.is_valid():
            shot = form.save()
            return redirect('shot_info', pk=shot.pk)
    else:
        form = ShotForm(instance=instance)

    projects = Project.objects.all()
    sequences = Sequence.objects.all()

    return render(request, 'core/add_shot.html', {
        'form': form,
        'projects': projects,
        'sequences': sequences,
    })

def list_shots(request):
    project_id = request.GET.get('project')
    sequence_id = request.GET.get('sequence')

    shots = Shot.objects.all()

    if project_id:
        shots = shots.filter(project_id=project_id)
    if sequence_id:
        shots = shots.filter(sequence_id=sequence_id)

    projects = Project.objects.all()
    sequences = Sequence.objects.all()

    context = {
        'shots': shots,
        'projects': projects,
        'sequences': sequences,
        'selected_project': project_id,
        'selected_sequence': sequence_id,
    }
    return render(request, "core/shot_grid.html", context)
# Delete Shot
def delete_shot(request, pk):
    shot = get_object_or_404(Shot, pk=pk)
    shot.delete()  # same for disk if mixin handles it
    return redirect('shot_list')


def shot_info(request, pk: int):
    shot = get_object_or_404(Shot, pk=pk)

    if request.method == 'POST':
        form = ShotForm(request.POST, request.FILES, instance=shot)
        if form.is_valid():
            form.save()
            return redirect('shot_info', pk=shot.pk)
    else:
        form = ShotForm(instance=shot)

    tasks = (
        Task.objects
        .filter(shot=shot)
        .select_related('artist', 'asset')
        .order_by('-updated_at')[:25]
    )

    shot_ct = ContentType.objects.get_for_model(Shot)
    publishes = (
        Publish.objects
        .filter(target_content_type=shot_ct, target_object_id=shot.pk)
        .select_related('created_by', 'task')
        .order_by('-published_at')[:10]
    )

    usages = shot.asset_usages.select_related('asset', 'publish').order_by('asset__code')

    context = {
        'shot': shot,
        'form': form,
        'tasks': tasks,
        'publishes': publishes,
        'usages': usages,
    }
    return render(request, 'core/shot_info.html', context)
