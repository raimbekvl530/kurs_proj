from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from friends.models import Friend
from chats.models import ChatRoom, Group, GroupMessage
from .openai_client import ask_chatgpt  
from django.db.models import Q
from .forms import GroupForm, GroupPhotoForm, GroupEditForm, AddMemberForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
def chat(request):
    user = request.user

    friends = Friend.objects.filter(
        Q(following=user) | Q(follower=user), 
        is_accepted=True
    ).select_related('following__profile', 'follower__profile')
    

    groups = Group.objects.filter(members=user).order_by('-created_at')


    for friend in friends:

        if friend.following == user:
            friend.chat_partner = friend.follower
        else:
            friend.chat_partner = friend.following

        friend.unread_msg = ChatRoom.objects.filter(
            receiver=user, 
            sender=friend.chat_partner, 
            unread_messages=False
        ).count()
        

        try:
            friend.last_message_added = ChatRoom.objects.filter(
                Q(sender=friend.chat_partner, receiver=user) | Q(sender=user, receiver=friend.chat_partner)
            ).latest('timestamp')
        except ChatRoom.DoesNotExist:
            friend.last_message_added = None


    for group in groups:
        try:
            group.last_message = GroupMessage.objects.filter(group=group).latest('timestamp')
        except GroupMessage.DoesNotExist:
            group.last_message = None
        

        group.members_count = group.members.count()

    return render(request, "chats/chat.html", {
        'friends': friends,
        'groups': groups,
    })

@login_required
def chat_detail(request, username):
    user = request.user
    friend = get_object_or_404(User, username=username)

    friendship = Friend.objects.filter(
        Q(following=user, follower=friend) | Q(following=friend, follower=user),
        is_accepted=True
    ).first()
    
    if not friendship:
        messages.error(request, "Вы не можете общаться с этим пользователем")
        return redirect('chats:chat')

    messages_list = ChatRoom.objects.filter(
        Q(sender=friend, receiver=user) | Q(sender=user, receiver=friend)
    ).order_by("timestamp")

    # Отмечаем сообщения как прочитанные
    ChatRoom.objects.filter(receiver=user, sender=friend, unread_messages=False).update(unread_messages=True)

    return render(request, "chats/chat_detail.html", {'friend': friend, 'messages': messages_list})

@csrf_exempt
@login_required
def upload_file_chat(request, username):
    """Обработка загрузки файлов в личном чате"""
    if request.method == 'POST':
        friend = get_object_or_404(User, username=username)
        
        # Проверяем дружбу
        friendship = Friend.objects.filter(
            Q(following=request.user, follower=friend) | Q(following=friend, follower=request.user),
            is_accepted=True
        ).first()
        
        if not friendship:
            return JsonResponse({'error': 'Нет доступа'}, status=403)
        
        file = request.FILES.get('file')
        message_text = request.POST.get('message', '').strip()
        
        if file:
            if file.size > 10 * 1024 * 1024:
                return JsonResponse({'error': 'Файл слишком большой (максимум 10MB)'}, status=400)
            
            chat_message = ChatRoom.objects.create(
                sender=request.user,
                receiver=friend,
                message=message_text,
                file=file
            )
            
            return JsonResponse({
                'success': True,
                'file_url': chat_message.file.url,
                'file_type': chat_message.file_type,
                'message': chat_message.message,
                'timestamp': chat_message.timestamp.strftime('%H:%M')
            })
        
        return JsonResponse({'error': 'Файл не найден'}, status=400)
    
    return JsonResponse({'error': 'Метод не поддерживается'}, status=405)

@login_required
def group_chat(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    
    if not group.members.filter(id=request.user.id).exists():
        messages.error(request, "У вас нет доступа к этой группе")
        return redirect('chats:chat')
    
    messages_list = GroupMessage.objects.filter(group=group).order_by('timestamp')

    if request.method == 'POST' and 'message' in request.POST:
        message_text = request.POST.get('message', '').strip()
        if message_text:
            GroupMessage.objects.create(
                group=group,
                sender=request.user,
                message=message_text
            )
            return redirect('chats:group_chat', group_id=group.id)
    
    return render(request, 'chats/group_chat.html', {
        'group': group,
        'messages': messages_list,
    })

@csrf_exempt
@login_required
def upload_file_group(request, group_id):
    """Обработка загрузки файлов в группе"""
    if request.method == 'POST':
        group = get_object_or_404(Group, id=group_id)
        
        # Проверяем доступ к группе
        if not group.members.filter(id=request.user.id).exists():
            return JsonResponse({'error': 'Нет доступа к группе'}, status=403)
        
        file = request.FILES.get('file')
        message_text = request.POST.get('message', '').strip()
        
        if file:
            # Проверяем размер файла 
            if file.size > 10 * 1024 * 1024:
                return JsonResponse({'error': 'Файл слишком большой (максимум 10MB)'}, status=400)
            

            group_message = GroupMessage.objects.create(
                group=group,
                sender=request.user,
                message=message_text,
                file=file
            )
            
            return JsonResponse({
                'success': True,
                'file_url': group_message.file.url,
                'file_type': group_message.file_type,
                'message': group_message.message,
                'timestamp': group_message.timestamp.strftime('%H:%M'),
                'sender': request.user.username
            })
        
        return JsonResponse({'error': 'Файл не найден'}, status=400)
    
    return JsonResponse({'error': 'Метод не поддерживается'}, status=405)


@login_required
def chat_with_gpt(request):
    response_text = ""
    if request.method == "POST":
        user_input = request.POST.get("message", "")
        if user_input:
            response_text = ask_chatgpt(user_input)
    return render(request, "chats/chatgpt.html", {
        "response": response_text,
    })

@login_required
def create_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.admin = request.user
            group.save()
            form.save_m2m()
            group.members.add(request.user)  
            messages.success(request, f'Группа "{group.name}" успешно создана!')
            return redirect('chats:group_detail', group_id=group.id)
    else:
        form = GroupForm()

        user_friends = Friend.objects.filter(
            Q(following=request.user) | Q(follower=request.user), 
            is_accepted=True
        )
        
        friend_users = []
        for friend in user_friends:
            if friend.following == request.user:
                friend_users.append(friend.follower)
            else:
                friend_users.append(friend.following)
        
        form.fields['members'].queryset = User.objects.filter(id__in=[f.id for f in friend_users])
    
    return render(request, 'chats/create_group.html', {'form': form})

@login_required
def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    
    if not group.members.filter(id=request.user.id).exists():
        messages.error(request, "У вас нет доступа к этой группе")
        return redirect('chats:chat')
    

    recent_messages = GroupMessage.objects.filter(group=group).order_by('-timestamp')[:10]
    
    return render(request, "chats/group_detail.html", {
        "group": group,
        "recent_messages": recent_messages,
        "is_admin": group.admin == request.user,
    })

@login_required
def leave_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    

    if not group.members.filter(id=request.user.id).exists():
        messages.error(request, "Вы не состоите в этой группе")
        return redirect('chats:chat')
    

    if group.admin == request.user:
        messages.error(request, "Вы не можете покинуть группу, так как являетесь её администратором")
        return redirect('chats:group_detail', group_id=group.id)
    

    group.members.remove(request.user)
    messages.success(request, f"Вы покинули группу '{group.name}'")
    
    return redirect('chats:chat')

@login_required
def add_member_to_group(request, group_id):
    """Добавление участника в группу (только админ)"""
    group = get_object_or_404(Group, id=group_id)
    

    if group.admin != request.user:
        messages.error(request, "Только администратор может добавлять участников")
        return redirect('chats:group_detail', group_id=group.id)
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user_to_add = get_object_or_404(User, id=user_id)
        
        if not group.members.filter(id=user_to_add.id).exists():
            group.members.add(user_to_add)
            messages.success(request, f"Пользователь {user_to_add.username} добавлен в группу")
        else:
            messages.info(request, f"Пользователь {user_to_add.username} уже в группе")
    
    return redirect('chats:group_detail', group_id=group.id)


@login_required
def edit_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    

    if group.admin != request.user:
        messages.error(request, "Только администратор может редактировать группу")
        return redirect('chats:group_detail', group_id=group.id)
    
    if request.method == 'POST':
        form = GroupEditForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, f'Информация о группе "{group.name}" обновлена!')
            return redirect('chats:group_detail', group_id=group.id)
    else:
        form = GroupEditForm(instance=group)
    
    return render(request, 'chats/edit_group.html', {
        'form': form,
        'group': group
    })

@login_required
def change_group_photo(request, group_id):

    group = get_object_or_404(Group, id=group_id)

    if group.admin != request.user:
        messages.error(request, "Только администратор может изменять фото группы")
        return redirect('chats:group_detail', group_id=group.id)
    
    if request.method == 'POST':
        form = GroupPhotoForm(request.POST, request.FILES, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, "Фото группы обновлено!")
            return redirect('chats:group_detail', group_id=group.id)
    else:
        form = GroupPhotoForm(instance=group)
    
    return render(request, 'chats/change_group_photo.html', {
        'form': form,
        'group': group
    })

@login_required
def remove_group_photo(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    

    if group.admin != request.user:
        messages.error(request, "Только администратор может удалять фото группы")
        return redirect('chats:group_detail', group_id=group.id)
    
    if group.photo:
        group.photo.delete()
        messages.success(request, "Фото группы удалено")
    else:
        messages.info(request, "У группы нет фото для удаления")
    
    return redirect('chats:group_detail', group_id=group.id)

@login_required
def manage_members(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    

    if group.admin != request.user:
        messages.error(request, "Только администратор может управлять участниками")
        return redirect('chats:group_detail', group_id=group.id)
    

    user_friends = Friend.objects.filter(
        Q(following=request.user) | Q(follower=request.user), 
        is_accepted=True
    )
    

    friend_ids = []
    for friend in user_friends:
        if friend.following == request.user:
            friend_ids.append(friend.follower.id)
        else:
            friend_ids.append(friend.following.id)
    

    current_member_ids = list(group.members.values_list('id', flat=True))
    available_friend_ids = [fid for fid in friend_ids if fid not in current_member_ids]
    

    if request.method == 'POST' and 'add_member' in request.POST:
        member_id = request.POST.get('member')
        if member_id:
            try:
                member = User.objects.get(id=member_id)

                if int(member_id) in available_friend_ids:
                    group.members.add(member)
                    messages.success(request, f"Пользователь {member.username} добавлен в группу")
                else:
                    messages.error(request, "Пользователь недоступен для добавления")
            except User.DoesNotExist:
                messages.error(request, "Пользователь не найден")
        
        return redirect('chats:manage_members', group_id=group.id)
    

    available_users = User.objects.filter(id__in=available_friend_ids)
    
    return render(request, 'chats/manage_members.html', {
        'group': group,
        'members': group.members.all(),
        'available_users': available_users,
    })

@login_required
def remove_member(request, group_id, user_id):
    """Удаление участника из группы (только админ)"""
    group = get_object_or_404(Group, id=group_id)
    member = get_object_or_404(User, id=user_id)
    

    if group.admin != request.user:
        messages.error(request, "Только администратор может удалять участников")
        return redirect('chats:group_detail', group_id=group.id)
    

    if member == request.user:
        messages.error(request, "Вы не можете удалить себя из группы")
        return redirect('chats:manage_members', group_id=group.id)
    

    if group.members.filter(id=member.id).exists():
        group.members.remove(member)
        messages.success(request, f"Пользователь {member.username} удален из группы")
    else:
        messages.error(request, "Пользователь не состоит в этой группе")
    
    return redirect('chats:manage_members', group_id=group.id)

@login_required
def delete_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    

    if group.admin != request.user:
        messages.error(request, "Только администратор может удалить группу")
        return redirect('chats:group_detail', group_id=group.id)
    
    if request.method == 'POST':
        group_name = group.name
        group.delete()
        messages.success(request, f'Группа "{group_name}" была удалена')
        return redirect('chats:chat')
    
    return render(request, 'chats/delete_group.html', {'group': group})