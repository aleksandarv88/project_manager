from django import forms
from .models import (
    Project,
    Asset,
    Sequence,
    Shot,
    Artist,
    Task,
)


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "name",
            "code",
            "description",
            "status",
            "base_path",
            "start_date",
            "due_date",
            "default_fps",
            "resolution_width",
            "resolution_height",
            "color_space",
            "delivery_notes",
            "image",
        ]
        widgets = {
            "base_path": forms.TextInput(attrs={"size": 50}),
            "description": forms.Textarea(attrs={"rows": 2}),
            "delivery_notes": forms.Textarea(attrs={"rows": 3}),
        }


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            "name",
            "code",
            "project",
            "asset_type",
            "category",
            "subtype",
            "status",
            "pipeline_step",
            "description",
            "frame_start",
            "frame_end",
            "fps",
            "image",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
        }


class SequenceForm(forms.ModelForm):
    class Meta:
        model = Sequence
        fields = [
            "project",
            "name",
            "code",
            "description",
            "status",
            "frame_start",
            "frame_end",
            "handles",
            "fps",
            "resolution_width",
            "resolution_height",
            "color_space",
            "image",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
        }


class ShotForm(forms.ModelForm):
    class Meta:
        model = Shot
        fields = [
            "project",
            "sequence",
            "name",
            "code",
            "description",
            "status",
            "frame_start",
            "frame_end",
            "handles",
            "cut_in",
            "cut_out",
            "fps",
            "resolution_width",
            "resolution_height",
            "color_space",
            "shot_type",
            "notes",
            "image",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sequence'].queryset = Sequence.objects.all().order_by("project__code", "code", "name")

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
        fields = ["username", "country", "years_experience", "private_email", "professional_email", "status", "image"]
        widgets = {
            "professional_email": forms.TextInput(attrs={"readonly": "readonly"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['professional_email'].disabled = True
        if self.instance and self.instance.pk:
            self.fields['professional_email'].initial = self.instance.professional_email
        else:
            self.fields['professional_email'].initial = ''
        if 'status' in self.fields and not self.instance.pk:
            self.fields['status'].initial = 'active'

    def save(self, commit=True):
        artist = super().save(commit=False)
        if artist.username:
            artist.professional_email = f"{artist.username}@fx3x.com"
        if commit:
            artist.save()
        return artist



class TaskForm(forms.ModelForm):
    task_type = forms.ChoiceField(choices=Task.TASK_TYPE_CHOICES, label="Department")
    task_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = Task
        fields = [
            "artist",
            "task_name",
            "task_type",
            "department",
            "asset",
            "sequence",
            "shot",
            "description",
            "notes",
            "status",
            "priority",
            "start_date",
            "due_date",
            "bid_hours",
            "actual_hours",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sequence'].queryset = Sequence.objects.all()
        self.fields['sequence'].empty_label = "-- Select Sequence --"
        self.fields['shot'].queryset = Shot.objects.none()
        self.fields['shot'].empty_label = "-- Select Shot --"
        self.fields["priority"].required = False
        self.fields["priority"].initial = Task._meta.get_field("priority").default

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
    task_type = forms.ChoiceField(choices=Task.TASK_TYPE_CHOICES, label="Department")
    task_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = Task
        fields = [
            "task_name",
            "task_type",
            "department",
            "description",
            "notes",
            "status",
            "priority",
            "start_date",
            "due_date",
            "bid_hours",
            "actual_hours",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["priority"].required = False
        self.fields["priority"].initial = Task._meta.get_field("priority").default
