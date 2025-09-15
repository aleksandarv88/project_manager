from django.contrib import admin
from .models import Project, Asset, Sequence, Shot

admin.site.register(Project)
admin.site.register(Asset)
admin.site.register(Sequence)
admin.site.register(Shot)
