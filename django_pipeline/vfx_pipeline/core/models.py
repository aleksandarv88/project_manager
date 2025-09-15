# /vfx_pipeline/core/models.py
import os
import shutil
from django.db import models

DEFAULT_BASE_PATH = r"D:\\"  # default base path for projects

# -------------------------
# Helper Mixin for disk folders
# -------------------------
class DiskFolderMixin(models.Model):
    class Meta:
        abstract = True

    folder_name = ""

    def get_folder_path(self):
        """Return the full path on disk for this object."""
        parent_path = getattr(self, "parent_path", DEFAULT_BASE_PATH)
        return os.path.join(parent_path, self.folder_name)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # create folder after saving
        folder_path = self.get_folder_path()
        os.makedirs(folder_path, exist_ok=True)

    def delete(self, *args, **kwargs):
        folder_path = self.get_folder_path()
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        super().delete(*args, **kwargs)

# -------------------------
# Project
# -------------------------
# models.py
class Project(DiskFolderMixin, models.Model):
    name = models.CharField(max_length=100)
    base_path = models.CharField(max_length=255, default=DEFAULT_BASE_PATH)
    image = models.ImageField(upload_to='projects', blank=True, null=True)  # add this

    folder_name = property(lambda self: self.name)

    @property
    def parent_path(self):
        return self.base_path

    def __str__(self):
        return self.name

    # Optionally, create folders automatically
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Create assets and sequences folders
        os.makedirs(os.path.join(self.get_folder_path(), 'assets'), exist_ok=True)
        os.makedirs(os.path.join(self.get_folder_path(), 'sequences'), exist_ok=True)

# -------------------------
# Asset
# -------------------------
class Asset(DiskFolderMixin, models.Model):
    ASSET_TYPES = [
        ('props', 'Props'),
        ('env', 'Environment'),
        ('vehicle', 'Vehicle'),
        ('fx', 'FX'),
        ('other', 'Other'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="assets")
    name = models.CharField(max_length=100)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES, default='other')
    image = models.ImageField(upload_to="assets", blank=True, null=True)

    folder_name = property(lambda self: self.name)

    @property
    def parent_path(self):
        return os.path.join(self.project.get_folder_path(), "assets")

    def __str__(self):
        return self.name
# -------------------------
# Sequence
# -------------------------
class Sequence(DiskFolderMixin, models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="sequences")
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="seq", blank=True, null=True)
    folder_name = property(lambda self: self.name)

    @property
    def parent_path(self):
        return os.path.join(self.project.get_folder_path(), "sequences")

    def __str__(self):
        return self.name


class Shot(DiskFolderMixin, models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="shots")
    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE, related_name="shots")
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="shot", blank=True, null=True)
    folder_name = property(lambda self: self.name)

    @property
    def parent_path(self):
        return os.path.join(self.sequence.get_folder_path(), "shots")

    def __str__(self):
        return self.name