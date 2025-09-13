from django.urls import path
from .views import item_list, home, add_item_view, delete_item_post

urlpatterns = [
    path('home/', home, name='home'),
    path('items/', item_list, name='item_list'),
    path('add/', add_item_view, name='add_item'),
    path('delete_post/', delete_item_post, name='delete_item_post'),
    
]
