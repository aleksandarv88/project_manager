from django.db import models
from django.utils import timezone
from .disk_folder_mixin import DiskFolderMixin
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.utils import create_shot_structure


class Shot(DiskFolderMixin, models.Model):
    STATUS_CHOICES = [
        ("not_started", "Not Started"),
        ("in_progress", "In Progress"),
        ("awaiting_client", "Awaiting Client"),
        ("approved", "Approved"),
        ("omit", "Omit"),
    ]

    project = models.ForeignKey(
        "core.Project",
        on_delete=models.CASCADE,
        related_name="shots",
    )
    sequence = models.ForeignKey("core.Sequence", on_delete=models.CASCADE, related_name="shots")
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="not_started")
    frame_start = models.IntegerField(default=1001)
    frame_end = models.IntegerField(default=1100)
    handles = models.PositiveIntegerField(default=8)
    fps = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    cut_in = models.IntegerField(blank=True, null=True)
    cut_out = models.IntegerField(blank=True, null=True)
    resolution_width = models.PositiveIntegerField(blank=True, null=True)
    resolution_height = models.PositiveIntegerField(blank=True, null=True)
    color_space = models.CharField(max_length=32, blank=True)
    shot_type = models.CharField(max_length=32, blank=True)
    notes = models.TextField(blank=True)
    image = models.ImageField(upload_to="shot", blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    folder_name = property(lambda self: self.code or self.name)

    class Meta:
        unique_together = ("sequence", "code")
        ordering = ["sequence", "code", "name"]

    @property
    def parent_path(self):
        return self.sequence.get_folder_path()

    def __str__(self):
        sequence_code = self.sequence.code or self.sequence.name
        return f"{sequence_code}_{self.code or self.name}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = (self.name or "").replace(" ", "").lower()
        if not self.fps:
            self.fps = self.sequence.fps if self.sequence else self.project.default_fps
        if not self.color_space:
            self.color_space = self.sequence.color_space or self.project.color_space
        if not self.resolution_width:
            self.resolution_width = self.sequence.resolution_width or self.project.resolution_width
        if not self.resolution_height:
            self.resolution_height = self.sequence.resolution_height or self.project.resolution_height
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)


@receiver(post_save, sender=Shot)
def create_shot_folders(sender, instance, created, **kwargs):
    if created:
        base_path = instance.sequence.get_folder_path()
        create_shot_structure(base_path, instance.folder_name)
