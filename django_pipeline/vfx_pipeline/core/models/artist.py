from django.db import models
from django.core.exceptions import ValidationError

class Artist(models.Model):
    username = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.username


class Task(models.Model):
    STATUS_CHOICES = [
        ("not_started", "Not Started"),
        ("wip", "Work In Progress"),
        ("internal_approved", "Approved Internally"),
        ("client_approved", "Approved by Client"),
        ("done", "Done"),
    ]

    artist = models.ForeignKey("core.Artist", on_delete=models.CASCADE, related_name="tasks")

    # A task can be assigned to an Asset OR to a Shot/Sequence, but not both
    asset = models.ForeignKey("core.Asset", on_delete=models.CASCADE, blank=True, null=True, related_name="tasks")
    sequence = models.ForeignKey("core.Sequence", on_delete=models.CASCADE, blank=True, null=True, related_name="tasks")
    shot = models.ForeignKey("core.Shot", on_delete=models.CASCADE, blank=True, null=True, related_name="tasks")

    task_type = models.CharField(max_length=100)  # e.g. Modeling, Texturing
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="not_started")

    def clean(self):
        """
        Enforce: either asset OR shot/sequence, not both,
        and not all empty.
        """
        if self.asset and (self.shot or self.sequence):
            raise ValidationError("A task can be assigned to either an Asset OR a Shot/Sequence, not both.")
        if not self.asset and not self.shot and not self.sequence:
            raise ValidationError("You must assign the task to an Asset OR a Shot/Sequence.")

    def __str__(self):
        if self.asset:
            return f"{self.task_type} on Asset {self.asset} for {self.artist}"
        elif self.shot:
            return f"{self.task_type} on Shot {self.shot} for {self.artist}"
        elif self.sequence:
            return f"{self.task_type} on Sequence {self.sequence} for {self.artist}"
        return f"{self.task_type} for {self.artist}"
