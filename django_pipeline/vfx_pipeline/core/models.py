import os
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.utils import create_shot_structure
import shutil

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
        parent_path = getattr(
            self,
            "parent_path",
            getattr(settings, "PIPELINE_ROOT", settings.BASE_DIR)
        )
        return os.path.join(parent_path, self.folder_name)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        folder_path = self.get_folder_path()
        os.makedirs(folder_path, exist_ok=True)

    def delete(self, *args, **kwargs):
        folder_path = self.get_folder_path()

        if os.path.exists(folder_path):
            # ✅ Safety: restrict to inside PIPELINE_ROOT instead of BASE_DIR
            root_dir = os.path.abspath(getattr(settings, "PIPELINE_ROOT", settings.BASE_DIR))
            folder_abs = os.path.abspath(folder_path)

            if folder_abs.startswith(root_dir):
                shutil.rmtree(folder_path)
            else:
                raise RuntimeError(f"Refusing to delete folder outside pipeline path: {folder_abs}")

        super().delete(*args, **kwargs)
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
class Asset(models.Model):
    ASSET_TYPES = [
        ('props', 'Props'),
        ('env', 'Environment'),
        ('vehicle', 'Vehicle'),
        ('fx', 'FX'),
        ('other', 'Other'),
    ]

    project = models.ForeignKey("Project", on_delete=models.CASCADE, related_name="assets")
    name = models.CharField(max_length=100)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES, default='other')
    image = models.ImageField(upload_to="assets", blank=True, null=True)

    folder_name = property(lambda self: self.name)

    @property
    def parent_path(self):
        return os.path.join(self.project.get_folder_path(), "assets")

    @property
    def asset_path(self):
        """Full path for this asset inside the project."""
        return os.path.join(self.parent_path, self.asset_type, self.name)

    def __str__(self):
        return self.name


# 🔹 Signal to auto-create the folder structure after saving a new asset
@receiver(post_save, sender=Asset)
def create_asset_folders(sender, instance, created, **kwargs):
    if created:
        base_path = instance.parent_path
        create_asset_structure(base_path, instance.asset_type, instance.name)
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
        # remove the extra "shots" folder
        return self.sequence.get_folder_path()

    def __str__(self):
        return self.name
    

@receiver(post_save, sender=Shot)
def create_shot_folders(sender, instance, created, **kwargs):
    if created:
        # The sequence folder is the parent
        base_path = instance.sequence.get_folder_path()
        create_shot_structure(base_path, instance.name)