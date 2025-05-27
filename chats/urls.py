from django.urls import path
from . import views

app_name = "chats"

urlpatterns = [
    path('', views.chat, name="chat"),
    path('chat/<str:username>/', views.chat_detail, name="chat_detail"),
    path('chat/<str:username>/upload/', views.upload_file_chat, name="upload_file_chat"),  # Новый маршрут
    path('chatgpt/', views.chat_with_gpt, name='chatgpt'),
    
    # Группы  базовые
    path('create-group/', views.create_group, name='create_group'),
    path('group/<int:group_id>/', views.group_detail, name='group_detail'),
    path('group/<int:group_id>/chat/', views.group_chat, name='group_chat'),
    path('group/<int:group_id>/upload/', views.upload_file_group, name='upload_file_group'),  # Новый маршрут
    path('group/<int:group_id>/leave/', views.leave_group, name='leave_group'),
    
    # Группы управление только для админов
    path('group/<int:group_id>/edit/', views.edit_group, name='edit_group'),
    path('group/<int:group_id>/change-photo/', views.change_group_photo, name='change_group_photo'),
    path('group/<int:group_id>/remove-photo/', views.remove_group_photo, name='remove_group_photo'),
    path('group/<int:group_id>/manage-members/', views.manage_members, name='manage_members'),
    path('group/<int:group_id>/remove-member/<int:user_id>/', views.remove_member, name='remove_member'),
    path('group/<int:group_id>/delete/', views.delete_group, name='delete_group'),
    

    path('group/<int:group_id>/add-member/', views.add_member_to_group, name='add_member_to_group'),
]