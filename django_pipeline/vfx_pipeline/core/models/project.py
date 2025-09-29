from django.db import models
import os
from django.utils import timezone
from .disk_folder_mixin import DiskFolderMixin

DEFAULT_BASE_PATH = r"D:\\"  # adjust as needed


class Project(DiskFolderMixin, models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("on_hold", "On Hold"),
        ("bidding", "Bidding"),
        ("completed", "Completed"),
        ("archived", "Archived"),
    ]

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=32, blank=True, null=True, unique=True)
    description = models.TextField(blank=True)
    base_path = models.CharField(max_length=255, default=DEFAULT_BASE_PATH)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    image = models.ImageField(upload_to='projects', blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    default_fps = models.DecimalField(max_digits=5, decimal_places=2, default=24.0)
    resolution_width = models.PositiveIntegerField(default=2048)
    resolution_height = models.PositiveIntegerField(default=858)
    color_space = models.CharField(max_length=32, blank=True, default="ACEScg")
    delivery_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    folder_name = property(lambda self: self.name)

    @property
    def parent_path(self):
        return self.base_path

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = (self.name or "").replace(" ", "").upper()[:8] or None
        if not self.color_space:
            self.color_space = "ACEScg"
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
        os.makedirs(os.path.join(self.get_folder_path(), 'assets'), exist_ok=True)
        os.makedirs(os.path.join(self.get_folder_path(), 'sequences'), exist_ok=True)
