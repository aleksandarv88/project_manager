from django import forms
from .models import Project, Asset, Sequence, Shot

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "image"]  # adjust based on your Project model fields

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['name', 'project', 'asset_type', 'image']  # include image

class SequenceForm(forms.ModelForm):
    class Meta:
        model = Sequence
        fields = ['project', 'name']

class ShotForm(forms.ModelForm):
    class Meta:
        model = Shot
        fields = ['sequence', 'name', 'image']