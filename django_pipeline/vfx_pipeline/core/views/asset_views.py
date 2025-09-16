from django.shortcuts import render, redirect, get_object_or_404
from core.models import Project, Asset
from core.forms import  AssetForm

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

def delete_asset(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    asset.delete()
    return redirect("asset_list")  # or wherever you want to go after deletion
