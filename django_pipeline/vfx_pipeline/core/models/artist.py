from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class Artist(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('vacation', 'On Vacation'),
    ]

    username = models.CharField(max_length=150, unique=True)
    country = models.CharField(max_length=100, blank=True)
    years_experience = models.PositiveIntegerField(default=0)
    private_email = models.EmailField(blank=True)
    professional_email = models.EmailField(blank=True)
    image = models.ImageField(upload_to='artists', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    joined_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if self.username:
            self.professional_email = f"{self.username}@fx3x.com"
        super().save(*args, **kwargs)



class Task(models.Model):
    STATUS_CHOICES = [
        ("not_started", "Not Started"),
        ("wip", "Work In Progress"),
        ("internal_approved", "Approved Internally"),
        ("client_approved", "Approved by Client"),
        ("done", "Done"),
    ]

    TASK_TYPE_CHOICES = [
        ("anim", "anim"),
        ("env", "env"),
        ("fx", "fx"),
        ("layout", "layout"),
        ("lgt", "lgt"),
        ("mod", "mod"),
        ("cfx", "cfx"),
        ("ldev", "ldev"),
    ]

    artist = models.ForeignKey("core.Artist", on_delete=models.CASCADE, related_name="tasks")

    # A task can be assigned to an Asset OR to a Shot/Sequence, but not both
    asset = models.ForeignKey("core.Asset", on_delete=models.CASCADE, blank=True, null=True, related_name="tasks")
    sequence = models.ForeignKey("core.Sequence", on_delete=models.CASCADE, blank=True, null=True, related_name="tasks")
    shot = models.ForeignKey("core.Shot", on_delete=models.CASCADE, blank=True, null=True, related_name="tasks")

    task_name = models.CharField(max_length=150, blank=True)
    task_type = models.CharField(max_length=100, choices=TASK_TYPE_CHOICES)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="not_started")

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

    def __str__(self):
        label = self.task_name or self.task_type
        if self.asset:
            return f"{label} on Asset {self.asset} for {self.artist}"
        elif self.shot:
            return f"{label} on Shot {self.shot} for {self.artist}"
        elif self.sequence:
            return f"{label} on Sequence {self.sequence} for {self.artist}"
        return f"{label} for {self.artist}"
