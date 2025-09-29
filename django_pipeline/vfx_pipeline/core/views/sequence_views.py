from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404

from core.forms import SequenceForm
from core.models import Project, Publish, Sequence, Shot, Task

# Sequence views
def list_sequences(request):
    project_id = request.GET.get('project')
    projects = Project.objects.all()
    sequences = Sequence.objects.all()
    if project_id:
        sequences = sequences.filter(project_id=project_id)
    return render(request, 'core/sequence_grid.html', {
        'projects': projects,
        'sequences': sequences,
        'selected_project': project_id
    })

def add_sequence(request,pk=None):
    instance = Sequence.objects.get(pk=pk) if pk else None
    if request.method == 'POST':
        form = SequenceForm(request.POST, request.FILES,instance=instance)
        if form.is_valid():
            sequence = form.save()
            return redirect('sequence_info', pk=sequence.pk)
    else:
        form = SequenceForm(instance=instance)
    return render(request, 'core/add_sequence.html', {'form': form})

def delete_sequence(request, pk):
    seq = get_object_or_404(Sequence, pk=pk)
    seq.delete()  # this will also call DiskFolderMixin logic if implemented
    return redirect('sequence_list')


def sequence_info(request, pk: int):
    sequence = get_object_or_404(Sequence, pk=pk)

    if request.method == 'POST':
        form = SequenceForm(request.POST, request.FILES, instance=sequence)
        if form.is_valid():
            form.save()
            return redirect('sequence_info', pk=sequence.pk)
    else:
        form = SequenceForm(instance=sequence)

    shots = sequence.shots.select_related('sequence', 'project').order_by('code', 'name')
    tasks = (
        Task.objects
        .filter(
            models.Q(sequence=sequence) | models.Q(shot__sequence=sequence)
        )
        .select_related('artist', 'shot', 'asset')
        .order_by('-updated_at')[:25]
    )

    seq_ct = ContentType.objects.get_for_model(Sequence)
    publishes = (
        Publish.objects
        .filter(target_content_type=seq_ct, target_object_id=sequence.pk)
        .select_related('created_by', 'task')
        .order_by('-published_at')[:10]
    )

    context = {
        'sequence': sequence,
        'form': form,
        'shots': shots,
        'tasks': tasks,
        'publishes': publishes,
    }
    return render(request, 'core/sequence_info.html', context)
