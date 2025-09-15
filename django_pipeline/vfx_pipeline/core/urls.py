from django.urls import path
from . import views

urlpatterns = [

    # Projects
    path('', views.project_list, name='project_list'),
    path('projects/add/', views.add_project, name='add_project'),
    path('projects/delete/<int:pk>/', views.delete_project, name='delete_project'),
    path('projects/edit/<int:pk>/', views.add_project, name='edit_project'),


    # Assets
    path('assets/', views.asset_list, name='asset_list'),
    path('assets/add/', views.add_asset, name='add_asset'),
    path('assets/delete/<int:pk>/', views.delete_asset, name='delete_asset'),
    path('assets/edit/<int:pk>/', views.add_asset, name='edit_asset'),


    # Sequences
    path('sequences/', views.list_sequences, name='sequence_list'),
    path('sequences/add/', views.add_sequence, name='add_sequence'),
    path('sequences/delete/<int:pk>/', views.delete_sequence, name='delete_sequence'),
    path('sequences/edit/<int:pk>/', views.add_sequence, name='edit_sequence'),


    # Shots
    path('shots/', views.list_shots, name='shot_list'),
    path('shots/add/', views.add_shot, name='add_shot'),
    path('shots/delete/<int:pk>/', views.delete_shot, name='delete_shot'),
    path('shots/edit/<int:pk>/', views.add_shot, name='edit_shot'),


    # API
    path('api/sequences/', views.api_sequences, name='api_sequences'),
]
