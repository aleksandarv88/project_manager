from __future__ import annotations

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


class AssetArtistAssignment(models.Model):
    asset = models.ForeignKey("core.Asset", on_delete=models.CASCADE, related_name="artist_assignments")
    artist = models.ForeignKey("core.Artist", on_delete=models.CASCADE, related_name="asset_assignments")
    role = models.CharField(max_length=64, blank=True)
    notes = models.TextField(blank=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("asset", "artist")

    def __str__(self) -> str:
        return f"{self.artist} on {self.asset}"


class Publish(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending", "Pending Review"),
        ("approved", "Approved"),
        ("deprecated", "Deprecated"),
        ("published", "Published"),
        ("failed", "Failed"),
    ]

    project = models.ForeignKey("core.Project", on_delete=models.CASCADE, related_name="publishes")
    target_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_object_id = models.PositiveIntegerField()
    target = GenericForeignKey("target_content_type", "target_object_id")
    task = models.ForeignKey("core.Task", on_delete=models.SET_NULL, blank=True, null=True, related_name="publishes")
    created_by = models.ForeignKey("core.Artist", on_delete=models.SET_NULL, blank=True, null=True, related_name="publishes_created")
    software = models.CharField(max_length=32, blank=True)
    label = models.CharField(max_length=128, blank=True)
    source_version = models.IntegerField(blank=True, null=True)
    source_iteration = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    item_usd_path = models.TextField(blank=True)
    asset_usd_path = models.TextField(blank=True)
    preview_path = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    published_at = models.DateTimeField(default=timezone.now)
    is_latest = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (
            "target_content_type",
            "target_object_id",
            "task",
        )
        ordering = ["-published_at"]

    def __str__(self) -> str:
        target_name = getattr(self.target, "code", None) or getattr(self.target, "name", None)
        if self.source_version is not None and self.source_iteration is not None:
            default_label = f"s{self.source_version:03d}-i{self.source_iteration:03d}"
        else:
            default_label = f"#{self.id}" if self.id else "Publish"
        label = self.label or default_label
        return f"{target_name or 'Publish'} {label}"


class PublishComponent(models.Model):
    COMPONENT_TYPES = [
        ("scene", "Scene File"),
        ("cache", "Cache"),
        ("preview", "Preview"),
        ("image", "Image"),
        ("data", "Data"),
    ]

    publish = models.ForeignKey(Publish, on_delete=models.CASCADE, related_name="components")
    name = models.CharField(max_length=128)
    component_type = models.CharField(max_length=32, choices=COMPONENT_TYPES, default="scene")
    file_path = models.CharField(max_length=512)
    file_size = models.BigIntegerField(blank=True, null=True)
    hash_md5 = models.CharField(max_length=64, blank=True)
    frame_start = models.IntegerField(blank=True, null=True)
    frame_end = models.IntegerField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["publish", "name"]

    def __str__(self) -> str:
        return f"{self.publish}::{self.name}"


class VersionLink(models.Model):
    LINK_TYPES = [
        ("dependency", "Dependency"),
        ("input", "Input"),
        ("upstream", "Upstream"),
        ("rendered_from", "Rendered From"),
    ]

    source = models.ForeignKey(Publish, on_delete=models.CASCADE, related_name="links_out")
    target = models.ForeignKey(Publish, on_delete=models.CASCADE, related_name="links_in")
    link_type = models.CharField(max_length=32, choices=LINK_TYPES, default="dependency")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("source", "target", "link_type")

    def __str__(self) -> str:
        return f"{self.source} -> {self.target} ({self.link_type})"


class ShotAssetUsage(models.Model):
    STATUS_CHOICES = [
        ("planned", "Planned"),
        ("in_progress", "In Progress"),
        ("approved", "Approved"),
        ("archived", "Archived"),
    ]

    shot = models.ForeignKey("core.Shot", on_delete=models.CASCADE, related_name="asset_usages")
    asset = models.ForeignKey("core.Asset", on_delete=models.CASCADE, related_name="shot_usages")
    publish = models.ForeignKey(Publish, on_delete=models.SET_NULL, blank=True, null=True, related_name="shot_usages")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planned")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("shot", "asset", "publish")

    def __str__(self) -> str:
        publish_label = self.publish.label if self.publish else "latest"
        return f"{self.asset} in {self.shot} ({publish_label})"
