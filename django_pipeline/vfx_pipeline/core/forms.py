from django import forms
from .models import Project, Asset, Sequence, Shot, Artist, Task


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


class ArtistForm(forms.ModelForm):
    class Meta:
        model = Artist
        fields = ["username"]


class TaskForm(forms.ModelForm):
    task_type = forms.ChoiceField(choices=Task.TASK_TYPE_CHOICES)
    task_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = Task
        fields = ["artist", "task_name", "asset", "sequence", "shot", "task_type", "description", "status"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sequence'].queryset = Sequence.objects.all()
        self.fields['sequence'].empty_label = "-- Select Sequence --"
        self.fields['shot'].queryset = Shot.objects.none()
        self.fields['shot'].empty_label = "-- Select Shot --"

        if 'sequence' in self.data:
            try:
                sequence_id = int(self.data.get('sequence'))
                self.fields['shot'].queryset = Shot.objects.filter(sequence_id=sequence_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.sequence:
            self.fields['shot'].queryset = self.instance.sequence.shots.all()

    def clean(self):
        cleaned_data = super().clean()
        asset = cleaned_data.get('asset')
        sequence = cleaned_data.get('sequence')
        shot = cleaned_data.get('shot')

        if asset and (sequence or shot):
            raise forms.ValidationError("Select either an asset or a sequence/shot, not both.")
        if not asset and not sequence and not shot:
            raise forms.ValidationError("Select an asset or a sequence/shot.")

        if shot:
            if sequence and shot.sequence_id != sequence.id:
                self.add_error('shot', 'Selected shot does not belong to the chosen sequence.')
                self.add_error('sequence', 'Selected sequence does not include this shot.')
                raise forms.ValidationError('Shot does not belong to the selected sequence.')
            cleaned_data['sequence'] = shot.sequence
        elif asset:
            cleaned_data['sequence'] = None
            cleaned_data['shot'] = None
        else:
            cleaned_data['shot'] = None

        return cleaned_data


class TaskUpdateForm(forms.ModelForm):
    task_type = forms.ChoiceField(choices=Task.TASK_TYPE_CHOICES)
    task_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = Task
        fields = ["task_name", "task_type", "description", "status"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2})
        }
