from django import forms
from django.contrib.auth.models import User
from .models import Group

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'members']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Например: Семья, Работа, Друзья...',
                'required': True
            }),
            'members': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '8',
                'style': 'height: 200px;'
            })
        }
        labels = {
            'name': 'Название группы',
            'members': 'Участники'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class GroupEditForm(forms.ModelForm):
    """Форма для редактирования основной информации группы"""
    class Meta:
        model = Group
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название группы',
                'required': True
            })
        }
        labels = {
            'name': 'Название группы'
        }

class GroupPhotoForm(forms.ModelForm):
    """Форма для загрузки фото группы"""
    class Meta:
        model = Group
        fields = ['photo']
        widgets = {
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
        labels = {
            'photo': 'Фото группы'
        }

class AddMemberForm(forms.Form):
    """Форма для добавления участника в группу"""
    member = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Выберите пользователя',
        empty_label='Выберите пользователя для добавления'
    )

    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('current_user', None)
        group = kwargs.pop('group', None)
        super().__init__(*args, **kwargs)
        
        if current_user and group:
            from friends.models import Friend
            from django.db.models import Q
            
            user_friends = Friend.objects.filter(
                Q(following=current_user) | Q(follower=current_user), 
                is_accepted=True
            )
            
            friend_users = []
            for friend in user_friends:
                if friend.following == current_user:
                    friend_users.append(friend.follower)
                else:
                    friend_users.append(friend.following)
            
            available_users = User.objects.filter(
                id__in=[f.id for f in friend_users]
            ).exclude(
                id__in=group.members.values_list('id', flat=True)
            )
            
            self.fields['member'].queryset = available_users


