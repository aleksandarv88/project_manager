from django.db import models
import os
from .disk_folder_mixin import DiskFolderMixin

DEFAULT_BASE_PATH = r"D:\\"  # adjust as needed

class Project(DiskFolderMixin, models.Model):
    name = models.CharField(max_length=100)
    base_path = models.CharField(max_length=255, default=DEFAULT_BASE_PATH)
    image = models.ImageField(upload_to='projects', blank=True, null=True)

    folder_name = property(lambda self: self.name)

    @property
    def parent_path(self):
        return self.base_path

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        os.makedirs(os.path.join(self.get_folder_path(), 'assets'), exist_ok=True)
        os.makedirs(os.path.join(self.get_folder_path(), 'sequences'), exist_ok=True)
