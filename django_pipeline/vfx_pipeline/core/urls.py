from django.urls import path
from . import views
from core.views.artist_views import artist_manager, artist_assignment, artist_info, update_task, delete_task
from core.views import api_views


urlpatterns = [

    # Projects
    path('', views.project_list, name='project_list'),
    path('projects/add/', views.add_project, name='add_project'),
    path('projects/delete/<int:pk>/', views.delete_project, name='delete_project'),
    path('projects/edit/<int:pk>/', views.add_project, name='edit_project'),
    path('projects/<int:pk>/', views.project_info, name='project_info'),


    # Assets
    path('assets/', views.asset_list, name='asset_list'),
    path('assets/add/', views.add_asset, name='add_asset'),
    path('assets/<int:asset_id>', views.asset_info, name='asset_info'),
    path('assets/delete/<int:pk>/', views.delete_asset, name='delete_asset'),
    path('assets/edit/<int:pk>/', views.add_asset, name='edit_asset'),


    # Sequences
    path('sequences/', views.list_sequences, name='sequence_list'),
    path('sequences/add/', views.add_sequence, name='add_sequence'),
    path('sequences/delete/<int:pk>/', views.delete_sequence, name='delete_sequence'),
    path('sequences/edit/<int:pk>/', views.add_sequence, name='edit_sequence'),
    path('sequences/<int:pk>/', views.sequence_info, name='sequence_info'),


    # Shots
    path('shots/', views.list_shots, name='shot_list'),
    path('shots/add/', views.add_shot, name='add_shot'),
    path('shots/delete/<int:pk>/', views.delete_shot, name='delete_shot'),
    path('shots/edit/<int:pk>/', views.add_shot, name='edit_shot'),
    path('shots/<int:pk>/', views.shot_info, name='shot_info'),

    path("artists/", artist_manager, name="artist_manager"),
    path("artists/assignment/", artist_assignment, name="artist_assignment"),
    path("artists/<int:artist_id>/", artist_info, name="artist_info"),
    path("tasks/<int:task_id>/update/", update_task, name="update_task"),
    path("tasks/<int:task_id>/delete/", delete_task, name="delete_task"),




    # API
    path('api/projects/', api_views.api_projects, name='api_projects'),
    path('api/assets/', api_views.api_assets, name='api_assets'),
    path('api/tags/', api_views.api_tags, name='api_tags'),
    path('api/sequences/', api_views.api_sequences, name='api_sequences'),
    path('api/shots/', api_views.api_shots, name='api_shots'),
    path('api/artists/', api_views.api_artists, name='api_artists'),
    path('api/tasks/', api_views.api_tasks, name='api_tasks'),
    path('api/scenes/', api_views.api_scenes, name='api_scenes'),
    path('api/scenes/next/', api_views.api_scenes_next, name='api_scenes_next'),
    path('api/scenes/record/', api_views.api_scenes_record, name='api_scenes_record'),
    path('api/publishes/', api_views.api_publishes, name='api_publishes'),
    path('api/publishes/next/', api_views.api_publishes_next, name='api_publishes_next'),
]
