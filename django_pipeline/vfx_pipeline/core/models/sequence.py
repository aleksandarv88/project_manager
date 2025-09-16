from django.db import models
import os
from .disk_folder_mixin import DiskFolderMixin

class Sequence(DiskFolderMixin, models.Model):
    project = models.ForeignKey(
        "core.Project",
        on_delete=models.CASCADE,
        related_name="sequences",
    )
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="seq", blank=True, null=True)
    folder_name = property(lambda self: self.name)

    @property
    def parent_path(self):
        return os.path.join(self.project.get_folder_path(), "sequences")

    def __str__(self):
        return self.name
