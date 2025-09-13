from django.db import models

class Item(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='items/', blank=True, null=True)  # stores uploaded images in media/items/

    def __str__(self):
        return self.name

