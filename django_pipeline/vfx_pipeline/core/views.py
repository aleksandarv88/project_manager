from django.shortcuts import render, redirect, get_object_or_404
from .models import Project, Asset, Sequence, Shot
from .forms import ProjectForm, AssetForm, SequenceForm, ShotForm
from django.http import JsonResponse
import os

# Project
def add_project(request, pk=None):
    instance = Project.objects.get(pk=pk) if pk else None

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('project_list')
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

def asset_list(request):
    project_id = request.GET.get('project')  # get selected project from query param
    projects = Project.objects.all()
    
    if project_id:
        assets = Asset.objects.filter(project_id=project_id)
    else:
        assets = Asset.objects.all()
    
    return render(request, 'core/asset_list.html', {
        'assets': assets,
        'projects': projects,
        'selected_project': int(project_id) if project_id else None
    })

def add_asset(request,pk=None):
    instance = Asset.objects.get(pk=pk) if pk else None
    if request.method == 'POST':
        form = AssetForm(request.POST, request.FILES, instance=instance)  # ← important: include request.FILES
        if form.is_valid():
            form.save()
            return redirect('asset_list')
    else:
        form = AssetForm(instance=instance)
    return render(request, 'core/add_asset.html', {'form': form})

def delete_asset(request, asset_id):
    asset = get_object_or_404(Asset, id=asset_id)
    asset.delete()
    return redirect('asset_list')



# Sequence views
def list_sequences(request):
    project_id = request.GET.get('project')
    projects = Project.objects.all()
    sequences = Sequence.objects.all()
    if project_id:
        sequences = sequences.filter(project_id=project_id)
    return render(request, 'core/sequence_list.html', {
        'projects': projects,
        'sequences': sequences,
        'selected_project': project_id
    })

def add_sequence(request,pk=None):
    instance = Sequence.objects.get(pk=pk) if pk else None
    if request.method == 'POST':
        form = SequenceForm(request.POST, request.FILES,instance=instance)  # <-- Add request.FILES here
        if form.is_valid():
            form.save()
            return redirect('sequence_list')
    else:
        form = SequenceForm(instance=instance)
    return render(request, 'core/add_sequence.html', {'form': form})

def delete_sequence(request, pk):
    seq = get_object_or_404(Sequence, pk=pk)
    seq.delete()  # this will also call DiskFolderMixin logic if implemented
    return redirect('sequence_list')

# Shot views
# List shots with project and sequence filtering
def add_shot(request,pk=None):
    instance = Shot.objects.get(pk=pk) if pk else None
    if request.method == 'POST':
        form = ShotForm(request.POST, request.FILES,instance=instance)
        if form.is_valid():
            form.save()  # <- this writes to the DB
            return redirect('shot_list')
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
    return render(request, "core/shot_list.html", context)
# Delete Shot
def delete_shot(request, pk):
    shot = get_object_or_404(Shot, pk=pk)
    shot.delete()  # same for disk if mixin handles it
    return redirect('shot_list')

def api_sequences(request):
    project_id = request.GET.get('project_id')
    if not project_id:
        return JsonResponse([], safe=False)
    sequences = Sequence.objects.filter(project_id=project_id).values('id', 'name')
    return JsonResponse(list(sequences), safe=False)



