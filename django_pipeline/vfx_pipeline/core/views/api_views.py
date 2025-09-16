from django.shortcuts import render, redirect, get_object_or_404
from core.models import Sequence
from django.http import JsonResponse


def api_sequences(request):
    project_id = request.GET.get('project_id')
    if not project_id:
        return JsonResponse([], safe=False)
    sequences = Sequence.objects.filter(project_id=project_id).values('id', 'name')
    return JsonResponse(list(sequences), safe=False)



