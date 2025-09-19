from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from core.models import Project, Asset, Sequence, Shot, Artist


def _delete_file(fieldfile) -> None:
    if not fieldfile:
        return
    file_name = getattr(fieldfile, "name", None)
    storage = getattr(fieldfile, "storage", None)
    if not file_name or storage is None:
        return
    if storage.exists(file_name):
        storage.delete(file_name)


def _delete_old_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        previous = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    old_file = getattr(previous, "image", None)
    new_file = getattr(instance, "image", None)
    if old_file and old_file != new_file:
        _delete_file(old_file)


@receiver(pre_save, sender=Project)
@receiver(pre_save, sender=Asset)
@receiver(pre_save, sender=Sequence)
@receiver(pre_save, sender=Shot)
@receiver(pre_save, sender=Artist)
def auto_delete_image_on_change(sender, instance, **kwargs):
    _delete_old_file_on_change(sender, instance, **kwargs)


@receiver(post_delete, sender=Project)
@receiver(post_delete, sender=Asset)
@receiver(post_delete, sender=Sequence)
@receiver(post_delete, sender=Shot)
@receiver(post_delete, sender=Artist)
def auto_delete_image_on_delete(sender, instance, **kwargs):
    _delete_file(getattr(instance, "image", None))
