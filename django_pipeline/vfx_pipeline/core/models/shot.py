from django.db import models
from .disk_folder_mixin import DiskFolderMixin
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.utils import create_shot_structure

class Shot(DiskFolderMixin, models.Model):
    project = models.ForeignKey(
        "core.Project",
        on_delete=models.CASCADE,
        related_name="shots",
    )
    sequence = models.ForeignKey("core.Sequence", on_delete=models.CASCADE, related_name="shots")
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="shot", blank=True, null=True)
    folder_name = property(lambda self: self.name)

    @property
    def parent_path(self):
        return self.sequence.get_folder_path()

    def __str__(self):
        return self.name


@receiver(post_save, sender=Shot)
def create_shot_folders(sender, instance, created, **kwargs):
    if created:
        base_path = instance.sequence.get_folder_path()
        create_shot_structure(base_path, instance.name)
