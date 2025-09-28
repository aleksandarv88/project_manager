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
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # <-- New field
    #updated_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # <-- New field

    @property
    def assigned_artists(self):
        """
        Returns a queryset of unique artists assigned to this asset via tasks.
        Assumes Task model has fields: asset (ForeignKey), artist (ForeignKey).
        """
        from core.models import task, artist  # Import here to avoid circular import
        Task = task.Task
        Artist = artist.Artist
        artist_ids = Task.objects.filter(asset=self).values_list('artist', flat=True).distinct()
        return Artist.objects.filter(id__in=artist_ids).values_list('username', flat=True).distinct()

    @property
    def assigned_artists_with_departments(self):
        """
        Returns a list of dicts: [{'username': ..., 'department': ...}, ...]
        for each unique (artist, department) assigned to this asset via tasks.
        """
        from core.models import task, artist
        Task = task.Task
        Artist = artist.Artist
        qs = Task.objects.filter(asset=self).select_related('artist').values('artist__username', 'task_type')
        # Remove duplicates (artist, department)
        seen = set()
        result = []
        for row in qs:
            key = (row['artist__username'], row['task_type'])
            if key not in seen:
                seen.add(key)
                result.append({'username': row['artist__username'], 'department': row['task_type']})
        return result
    
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
