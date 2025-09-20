from django.shortcuts import render, redirect, get_object_or_404
from core.models import Project, Sequence, Shot
from core.forms import ShotForm


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
    return render(request, "core/shot_grid.html", context)
# Delete Shot
def delete_shot(request, pk):
    shot = get_object_or_404(Shot, pk=pk)
    shot.delete()  # same for disk if mixin handles it
    return redirect('shot_list')
