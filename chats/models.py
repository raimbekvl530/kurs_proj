from django.db import models
from friends.models import Friend
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
import os

User = get_user_model()

def user_file_path(instance, filename):
    """Функция для создания пути к файлу пользователя"""
    return f'chat_files/{instance.sender.username}/{filename}'

class ChatRoom(models.Model):
    sender = models.ForeignKey(User, related_name="sender", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="receiver", on_delete=models.CASCADE)
    message = models.TextField(blank=True, null=True)  # Теперь может быть пустым если есть файл
    file = models.FileField(upload_to=user_file_path, blank=True, null=True)  # Новое поле для файлов
    file_type = models.CharField(max_length=20, blank=True, null=True)  # image, video, document
    timestamp = models.DateTimeField(auto_now_add=True)
    unread_messages = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.sender.username} send to {self.receiver.username}"
    
    def get_file_type(self):
        """Определяет тип файла по расширению"""
        if not self.file:
            return None
        
        file_extension = os.path.splitext(self.file.name)[1].lower()
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']
        
        if file_extension in image_extensions:
            return 'image'
        elif file_extension in video_extensions:
            return 'video'
        else:
            return 'document'
    
    def save(self, *args, **kwargs):
        """Автоматически определяем тип файла при сохранении"""
        if self.file:
            self.file_type = self.get_file_type()
        super().save(*args, **kwargs)

class Group(models.Model):
    name = models.CharField(max_length=100)
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_groups')
    members = models.ManyToManyField(User, related_name='chat_groups')
    photo = models.ImageField(upload_to='group_photos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
        
    def get_photo_url(self):
        """Возвращает URL фото группы или None"""
        if self.photo:
            return self.photo.url
        return None

def group_file_path(instance, filename):
    """Функция для создания пути к файлу группы"""
    return f'group_files/{instance.group.name}/{filename}'

class GroupMessage(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(blank=True, null=True)  # Теперь может быть пустым если есть файл
    file = models.FileField(upload_to=group_file_path, blank=True, null=True)  # Новое поле для файлов
    file_type = models.CharField(max_length=20, blank=True, null=True)  # image, video, document
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender.username} in {self.group.name}: {self.message[:50]}"
    
    def get_file_type(self):
        """Определяет тип файла по расширению"""
        if not self.file:
            return None
        
        file_extension = os.path.splitext(self.file.name)[1].lower()
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']
        
        if file_extension in image_extensions:
            return 'image'
        elif file_extension in video_extensions:
            return 'video'
        else:
            return 'document'
    
    def save(self, *args, **kwargs):
        """Автоматически определяем тип файла при сохранении"""
        if self.file:
            self.file_type = self.get_file_type()
        super().save(*args, **kwargs)