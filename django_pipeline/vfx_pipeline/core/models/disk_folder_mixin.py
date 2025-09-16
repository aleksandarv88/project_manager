import os
import shutil
from django.conf import settings
from django.db import models

class DiskFolderMixin(models.Model):
    class Meta:
        abstract = True

    folder_name = ""

    def get_folder_path(self):
        parent_path = getattr(
            self,
            "parent_path",
            getattr(settings, "PIPELINE_ROOT", settings.BASE_DIR)
        )
        return os.path.join(parent_path, self.folder_name)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        folder_path = self.get_folder_path()
        os.makedirs(folder_path, exist_ok=True)

    def delete(self, *args, **kwargs):
        folder_path = self.get_folder_path()

        if os.path.exists(folder_path):
            root_dir = os.path.abspath(getattr(settings, "PIPELINE_ROOT", settings.BASE_DIR))
            folder_abs = os.path.abspath(folder_path)

            if folder_abs.startswith(root_dir):
                shutil.rmtree(folder_path)
            else:
                raise RuntimeError(f"Refusing to delete folder outside pipeline path: {folder_abs}")

        super().delete(*args, **kwargs)
