from django import forms
from .models import Project, Asset, Sequence, Shot

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'image', 'base_path']  # add base_path here
        widgets = {
            'base_path': forms.TextInput(attrs={'value': 'D:\\', 'size': 50})
        }

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['name', 'project', 'asset_type', 'image']  # include image

class SequenceForm(forms.ModelForm):
    class Meta:
        model = Sequence
        fields = ['project', 'name', 'image']
        

class ShotForm(forms.ModelForm):
    class Meta:
        model = Shot
        fields = ['project', 'sequence', 'name', 'image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sequence'].queryset = Sequence.objects.none()

        if 'project' in self.data:
            try:
                project_id = int(self.data.get('project'))
                self.fields['sequence'].queryset = Sequence.objects.filter(project_id=project_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['sequence'].queryset = self.instance.project.sequences.all()
