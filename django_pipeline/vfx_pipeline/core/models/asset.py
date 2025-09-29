from django.db import models
import os
from django.utils import timezone
from .disk_folder_mixin import DiskFolderMixin
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.utils import create_asset_structure


class Asset(DiskFolderMixin, models.Model):
    ASSET_TYPES = [
        ("character", "Character"),
        ("creature", "Creature"),
        ("props", "Props"),
        ("env", "Environment"),
        ("vehicle", "Vehicle"),
        ("fx", "FX"),
        ("matte", "Matte Painting"),
        ("rig", "Rig"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("design", "Design"),
        ("model", "Model"),
        ("texture", "Texture"),
        ("lookdev", "Look Dev"),
        ("rigging", "Rigging"),
        ("approved", "Approved"),
        ("archived", "Archived"),
    ]

    project = models.ForeignKey("core.Project", on_delete=models.CASCADE, related_name="assets")
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=64, blank=True)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES, default="other")
    category = models.CharField(max_length=32, blank=True)
    subtype = models.CharField(max_length=32, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="design")
    pipeline_step = models.CharField(max_length=32, blank=True)
    description = models.TextField(blank=True)
    frame_start = models.IntegerField(blank=True, null=True)
    frame_end = models.IntegerField(blank=True, null=True)
    fps = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    image = models.ImageField(upload_to="assets", blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("project", "code")
        ordering = ["project", "code", "name"]

    @property
    def assigned_artists(self):
        """Return usernames for artists with tasks on this asset."""
        from core.models import task, artist  # Avoid circular import

        Task = task.Task
        Artist = artist.Artist
        artist_ids = Task.objects.filter(asset=self).values_list("artist", flat=True).distinct()
        return Artist.objects.filter(id__in=artist_ids).values_list("username", flat=True).distinct()

    @property
    def assigned_artists_with_departments(self):
        """Return unique list of artists and departments."""
        from core.models import task, artist

        Task = task.Task
        Artist = artist.Artist
        qs = Task.objects.filter(asset=self).select_related("artist").values("artist__username", "task_type")
        seen = set()
        result = []
        for row in qs:
            key = (row["artist__username"], row["task_type"])
            if key not in seen:
                seen.add(key)
                result.append({"username": row["artist__username"], "department": row["task_type"]})
        return result

    @property
    def folder_name(self):
        code_part = (self.code or self.name).replace(" ", "_")
        asset_type = (self.asset_type or "other").strip()
        return os.path.join(asset_type, code_part)

    @property
    def parent_path(self):
        return os.path.join(self.project.get_folder_path(), "assets")

    def __str__(self):
        return self.code or self.name

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = (self.name or "").replace(" ", "_" ).lower()
        if not self.fps:
            self.fps = self.project.default_fps
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)


@receiver(post_save, sender=Asset)
def create_asset_folders(sender, instance, created, **kwargs):
    if created:
        base_path = instance.parent_path
        create_asset_structure(base_path, instance.asset_type, instance.code or instance.name)
