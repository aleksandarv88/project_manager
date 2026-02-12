from django.contrib import admin

from .models import (
    Asset,
    AssetArtistAssignment,
    AssetTag,
    Artist,
    Project,
    Publish,
    PublishComponent,
    Sequence,
    SequenceTag,
    Shot,
    ShotAssetUsage,
    ShotTag,
    Tag,
    Task,
    TaskAssignment,
    VersionLink,
)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "status", "start_date", "due_date")
    search_fields = ("name", "code")
    list_filter = ("status",)


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "project", "asset_type", "status")
    search_fields = ("name", "code")
    list_filter = ("project", "asset_type", "status")


@admin.register(Sequence)
class SequenceAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "project", "status")
    search_fields = ("name", "code")
    list_filter = ("project", "status")


@admin.register(Shot)
class ShotAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "sequence", "project", "status")
    search_fields = ("name", "code")
    list_filter = ("project", "sequence", "status")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("task_name", "task_type", "department", "status", "priority", "artist")
    search_fields = ("task_name", "task_type", "department")
    list_filter = ("status", "task_type", "department", "priority")


admin.site.register(Artist)
admin.site.register(Tag)
admin.site.register(AssetTag)
admin.site.register(SequenceTag)
admin.site.register(ShotTag)
admin.site.register(TaskAssignment)
admin.site.register(AssetArtistAssignment)
@admin.register(Publish)
class PublishAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "task",
        "project",
        "status",
        "source_version",
        "source_iteration",
        "created_at",
    )
    search_fields = ("label", "task__task_name", "task__id", "project__name")
    list_filter = ("status", "software", "created_at")


admin.site.register(PublishComponent)
admin.site.register(VersionLink)
admin.site.register(ShotAssetUsage)
