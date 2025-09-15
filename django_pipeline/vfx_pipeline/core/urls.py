from django.urls import path
from . import views

urlpatterns = [

    path('', views.project_list, name='project_list'),  # existing
    path('add/', views.add_project, name='add_project'),  # existing
    path('delete/<int:pk>/', views.delete_project, name='delete_project'),  # existing

    path('assets/', views.asset_list, name='asset_list'),
    path('assets/add/', views.add_asset, name='add_asset'),
    path('assets/delete/<int:asset_id>/', views.delete_asset, name='delete_asset'),

    path('sequences/', views.list_sequences, name='sequence_list'),
    path('sequences/add/', views.add_sequence, name='add_sequence'),
    path('shots/', views.list_shots, name='shot_list'),
    path('api/sequences/', views.api_sequences, name='api_sequences'),
    path('shots/add/', views.add_shot, name='add_shot'),
    path('sequences/delete/<int:pk>/', views.delete_sequence, name='delete_sequence'),
    path('shots/delete/<int:pk>/', views.delete_shot, name='delete_shot'),


]
