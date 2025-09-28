from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class Artist(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("idle", "Idle"),
        ("inactive", "Inactive"),
        ("vacation", "On Vacation"),
    ]

    username = models.CharField(max_length=150, unique=True)
    country = models.CharField(max_length=100, blank=True)
    years_experience = models.PositiveIntegerField(default=0)
    private_email = models.EmailField(blank=True)
    professional_email = models.EmailField(blank=True)
    image = models.ImageField(upload_to='artists', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    joined_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if self.username:
            self.professional_email = f"{self.username}@fx3x.com"
        super().save(*args, **kwargs)




