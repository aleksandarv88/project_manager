from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class Task(models.Model):
    STATUS_CHOICES = [
        ("not_started", "Not Started"),
        ("wip", "Work In Progress"),
        ("internal_approved", "Approved Internally"),
        ("client_approved", "Approved by Client"),
        ("done", "Done"),
        ("on_hold", "On Hold"),
    ]

    TASK_TYPE_CHOICES = [
        ("anim", "Animation"),
        ("env", "Environment"),
        ("fx", "FX"),
        ("layout", "Layout"),
        ("lgt", "Lighting"),
        ("mod", "Model"),
        ("cfx", "Character FX"),
        ("ldev", "LookDev"),
        ("comp", "Compositing"),
        ("matte", "Matte"),
    ]

    PRIORITY_CHOICES = [
        (10, "Critical"),
        (20, "High"),
        (50, "Normal"),
        (80, "Low"),
    ]

    artist = models.ForeignKey("core.Artist", on_delete=models.CASCADE, related_name="tasks", blank=True, null=True)

    # A task can be assigned to an Asset OR to a Shot/Sequence, but not both
    asset = models.ForeignKey("core.Asset", on_delete=models.CASCADE, blank=True, null=True, related_name="tasks")
    sequence = models.ForeignKey("core.Sequence", on_delete=models.CASCADE, blank=True, null=True, related_name="tasks")
    shot = models.ForeignKey("core.Shot", on_delete=models.CASCADE, blank=True, null=True, related_name="tasks")

    task_name = models.CharField(max_length=150, blank=True)
    task_type = models.CharField(max_length=100, choices=TASK_TYPE_CHOICES)
    department = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="not_started")
    status_changed_at = models.DateTimeField(default=timezone.now)
    priority = models.PositiveSmallIntegerField(choices=PRIORITY_CHOICES, default=50)
    bid_hours = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-priority", "task_type", "task_name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = self.status

    def clean(self):
        super().clean()

        assigning_asset = self.asset is not None
        assigning_sequence = self.sequence is not None
        assigning_shot = self.shot is not None

        if assigning_asset and (assigning_sequence or assigning_shot):
            raise ValidationError("A task can be assigned to either an Asset OR a Shot/Sequence, not both.")
        if not assigning_asset and not assigning_sequence and not assigning_shot:
            raise ValidationError("You must assign the task to an Asset OR a Shot/Sequence.")

        if assigning_shot:
            if assigning_sequence and self.sequence_id != self.shot.sequence_id:
                raise ValidationError("Selected shot must belong to the chosen sequence.")
            self.sequence = self.shot.sequence
        elif assigning_asset:
            self.sequence = None
            self.shot = None
        elif assigning_sequence:
            self.shot = None

        if not self.department:
            self.department = self.task_type

    def save(self, *args, **kwargs):
        if self.status != self._original_status:
            self.status_changed_at = timezone.now()
            if self.status == "done" and not self.completed_at:
                self.completed_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
        self._original_status = self.status

    def __str__(self):
        label = self.task_name or self.task_type
        if self.asset:
            return f"{label} on Asset {self.asset}"
        if self.shot:
            return f"{label} on Shot {self.shot}"
        if self.sequence:
            return f"{label} on Sequence {self.sequence}"
        return label


class TaskAssignment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="assignments")
    artist = models.ForeignKey("core.Artist", on_delete=models.CASCADE, related_name="task_assignments")
    role = models.CharField(max_length=64, blank=True)
    responsibility = models.PositiveSmallIntegerField(default=100, help_text="Percent responsibility")
    is_lead = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("task", "artist")

    def __str__(self) -> str:
        return f"{self.artist} on {self.task}"
