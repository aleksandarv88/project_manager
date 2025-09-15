import os
import shutil
from django.conf import settings
from django.db import models

class Project(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='projects/', blank=True, null=True)

    # base path on disk (can be set before creating)
    base_path = os.path.join(settings.MEDIA_ROOT, 'projects')

    def save(self, *args, **kwargs):
        # Save DB entry first
        super().save(*args, **kwargs)
        # Create folder on disk
        folder_path = os.path.join(self.base_path, self.name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    def delete(self, *args, **kwargs):
        # Delete folder on disk
        folder_path = os.path.join(self.base_path, self.name)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        # Delete DB entry
        super().delete(*args, **kwargs)

class Asset(models.Model):
    ASSET_TYPES = [
        ('CHAR', 'Character'),
        ('PROP', 'Prop'),
        ('SET', 'Set'),
        ('VEH', 'Vehicle'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    asset_type = models.CharField(max_length=10, choices=ASSET_TYPES, default='PROP')
    image = models.ImageField(upload_to='assets/', null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.project.name})"


class Sequence(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sequences')
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.project.name} - {self.name}"

class Shot(models.Model):
    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE, related_name='shots')
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='shots/', blank=True, null=True)  # optional

    def __str__(self):
        return f"{self.sequence.name} - {self.name}"
