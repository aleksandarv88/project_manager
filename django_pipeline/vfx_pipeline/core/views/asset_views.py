from django.shortcuts import render, redirect, get_object_or_404

from core.forms import AssetForm
from core.models import Asset, Project, AssetVersion


def asset_list(request):
    project_id = request.GET.get('project')
    projects = Project.objects.all()

    if project_id:
        assets = Asset.objects.filter(project_id=project_id)
    else:
        assets = Asset.objects.all()

    return render(
        request,
        'core/asset_grid.html',
        {
            'assets': assets,
            'projects': projects,
            'selected_project': int(project_id) if project_id else None,
        },
    )


def add_asset(request, pk=None):
    instance = Asset.objects.get(pk=pk) if pk else None
    if request.method == 'POST':
        form = AssetForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            asset = form.save()
            return redirect('asset_info', asset_id=asset.pk)
    else:
        form = AssetForm(instance=instance)
    return render(request, 'core/add_asset.html', {'form': form})


def delete_asset(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    asset.delete()
    return redirect('asset_list')


def asset_info(request, asset_id):
    asset = get_object_or_404(Asset, pk=asset_id)
    if request.method == "POST":
        form = AssetForm(request.POST, request.FILES, instance=asset)
        if form.is_valid():
            form.save()
            return redirect('asset_info', asset_id=asset.id)
    else:
        form = AssetForm(instance=asset)

    versions = AssetVersion.objects.filter(asset=asset).prefetch_related("textures").order_by("-version", "-registered_at", "-id")
    selected_version = None
    selected_version_id = request.GET.get("version")
    if selected_version_id:
        selected_version = versions.filter(id=selected_version_id).first()
    if selected_version is None:
        selected_version = versions.first()

    return render(
        request,
        "core/asset_info.html",
        {
            "asset": asset,
            "form": form,
            "versions": versions,
            "selected_version": selected_version,
        },
    )
