from django.shortcuts import render, redirect, get_object_or_404
from core.models import Project
from core.forms import ProjectForm

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