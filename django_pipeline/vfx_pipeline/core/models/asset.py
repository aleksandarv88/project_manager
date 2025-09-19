from django.db import models
import os
from .disk_folder_mixin import DiskFolderMixin
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.utils import create_asset_structure

class Asset(DiskFolderMixin, models.Model):
    ASSET_TYPES = [
        ('props', 'Props'),
        ('env', 'Environment'),
        ('vehicle', 'Vehicle'),
        ('fx', 'FX'),
        ('other', 'Other'),
    ]
    project = models.ForeignKey("core.Project", on_delete=models.CASCADE, related_name="assets")
    name = models.CharField(max_length=100)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES, default='other')
    image = models.ImageField(upload_to="assets", blank=True, null=True)

    @property
    def folder_name(self):
        asset_type = (self.asset_type or 'other').strip()
        return os.path.join(asset_type, self.name)

    @property
    def parent_path(self):
        return os.path.join(self.project.get_folder_path(), "assets")

    def __str__(self):
        return self.name


@receiver(post_save, sender=Asset)
def create_asset_folders(sender, instance, created, **kwargs):
    if created:
        base_path = instance.parent_path
        create_asset_structure(base_path, instance.asset_type, instance.name)
