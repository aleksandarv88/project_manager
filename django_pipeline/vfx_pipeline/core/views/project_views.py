from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404

from core.forms import ProjectForm
from core.models import Asset, Project, Publish, Sequence, Shot, Task

# Project
def add_project(request, pk=None):
    instance = Project.objects.get(pk=pk) if pk else None

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            target = instance or form.instance
            return redirect('project_info', pk=target.pk)
    else:
        form = ProjectForm(instance=instance)

    return render(request, 'core/add_project.html', {'form': form})


def delete_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == "POST":
        project.delete()
        return redirect("project_list")
    return render(request, "core/delete_project.html", {"project": project})

def project_list(request):
    projects = Project.objects.all()
    return render(request, "core/project_list.html", {"projects": projects})


def project_info(request, pk: int):
    project = get_object_or_404(Project, pk=pk)

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            return redirect('project_info', pk=project.pk)
    else:
        form = ProjectForm(instance=project)

    sequences = project.sequences.select_related('project').order_by('code', 'name')
    shots = project.shots.select_related('sequence').order_by('sequence__code', 'code')[:25]
    assets = project.assets.order_by('code', 'name')[:25]

    project_ct = ContentType.objects.get_for_model(Project)
    publishes = (
        Publish.objects
        .filter(target_content_type=project_ct, target_object_id=project.pk)
        .select_related('created_by', 'task')
        .order_by('-published_at')[:10]
    )

    tasks = (
        Task.objects
        .filter(
            models.Q(asset__project=project)
            | models.Q(sequence__project=project)
            | models.Q(shot__project=project)
        )
        .select_related('artist', 'asset', 'sequence', 'shot')
        .order_by('-updated_at')[:20]
    )

    context = {
        'project': project,
        'form': form,
        'sequences': sequences,
        'shots': shots,
        'assets': assets,
        'publishes': publishes,
        'tasks': tasks,
    }
    return render(request, 'core/project_info.html', context)
