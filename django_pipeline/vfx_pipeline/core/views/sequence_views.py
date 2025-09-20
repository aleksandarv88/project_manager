from django.shortcuts import render, redirect, get_object_or_404
from core.models import Project, Sequence
from core.forms import SequenceForm

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