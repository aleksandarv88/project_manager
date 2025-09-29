from django.db import models
import os
from django.utils import timezone
from .disk_folder_mixin import DiskFolderMixin


class Sequence(DiskFolderMixin, models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("on_hold", "On Hold"),
        ("completed", "Completed"),
    ]

    project = models.ForeignKey(
        "core.Project",
        on_delete=models.CASCADE,
        related_name="sequences",
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=32, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    frame_start = models.IntegerField(default=1001)
    frame_end = models.IntegerField(default=1100)
    handles = models.PositiveIntegerField(default=8)
    fps = models.DecimalField(max_digits=5, decimal_places=2, default=24.0)
    resolution_width = models.PositiveIntegerField(blank=True, null=True)
    resolution_height = models.PositiveIntegerField(blank=True, null=True)
    color_space = models.CharField(max_length=32, blank=True)
    image = models.ImageField(upload_to="seq", blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    folder_name = property(lambda self: self.code or self.name)

    class Meta:
        unique_together = ("project", "code")
        ordering = ["project", "code", "name"]

    @property
    def parent_path(self):
        return os.path.join(self.project.get_folder_path(), "sequences")

    def __str__(self):
        return f"{self.project.code or self.project.name}-{self.code or self.name}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = (self.name or "").replace(" ", "").lower()
        if not self.fps and self.project:
            self.fps = self.project.default_fps
        if not self.color_space and self.project:
            self.color_space = self.project.color_space
        if not self.resolution_width and self.project:
            self.resolution_width = self.project.resolution_width
        if not self.resolution_height and self.project:
            self.resolution_height = self.project.resolution_height
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
