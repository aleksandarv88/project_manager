from django.shortcuts import render, redirect, get_object_or_404
from .models import Project, Asset, Sequence, Shot
from .forms import ProjectForm, AssetForm, SequenceForm, ShotForm
import os

def add_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  # disk folder creation happens in Project.save()
            return redirect('project_list')
    else:
        form = ProjectForm()
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

def add_asset(request):
    if request.method == 'POST':
        form = AssetForm(request.POST, request.FILES)  # ← important: include request.FILES
        if form.is_valid():
            form.save()
            return redirect('asset_list')
    else:
        form = AssetForm()
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

def add_sequence(request):
    if request.method == 'POST':
        form = SequenceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('sequence_list')
    else:
        form = SequenceForm()
    return render(request, 'core/add_sequence.html', {'form': form})

# Shot views
def list_shots(request):
    sequence_id = request.GET.get('sequence')
    sequences = Sequence.objects.all()
    shots = Shot.objects.all()
    if sequence_id:
        shots = shots.filter(sequence_id=sequence_id)
    return render(request, 'core/shot_list.html', {
        'sequences': sequences,
        'shots': shots,
        'selected_sequence': sequence_id
    })

def add_shot(request):
    if request.method == 'POST':
        form = ShotForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('shot_list')
    else:
        form = ShotForm()
    return render(request, 'core/add_shot.html', {'form': form})
