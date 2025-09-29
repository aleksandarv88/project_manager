from __future__ import annotations

from django.db import models
from django.utils import timezone


class Tag(models.Model):
    name = models.CharField(max_length=64, unique=True)
    category = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=16, blank=True, help_text="Optional hex color for UI chips")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class AssetTag(models.Model):
    asset = models.ForeignKey("core.Asset", on_delete=models.CASCADE, related_name="asset_tags")
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="asset_tags")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("asset", "tag")


class ShotTag(models.Model):
    shot = models.ForeignKey("core.Shot", on_delete=models.CASCADE, related_name="shot_tags")
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="shot_tags")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("shot", "tag")


class SequenceTag(models.Model):
    sequence = models.ForeignKey("core.Sequence", on_delete=models.CASCADE, related_name="sequence_tags")
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="sequence_tags")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("sequence", "tag")
