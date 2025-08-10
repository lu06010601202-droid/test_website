from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Prefetch
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from datetime import timedelta
from .models import Post, Comment, Category, UserProfile, Like, Notification, Report, Message, Follow, Tag, UserActivity, SiteStatistics
from .forms import PostForm, CommentForm, UserProfileForm, CustomUserCreationForm, ReportForm, MessageForm, FollowForm, TagForm
from .admin_forms import DeletePostForm, DeleteCommentForm, BanUserForm, UnbanUserForm
from .decorators import staff_required, author_required
from .utils.helpers import (
    get_cached_data, update_post_views, create_notification, 
    record_user_activity, can_delete_within_time_limit, get_paginated_queryset
)
from django.utils.html import strip_tags

def welcome(request):
    """欢迎页面视图"""
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'community/welcome.html')

@cache_page(60 * 5)  # 缓存5分钟
def home(request):
    """首页视图"""
    # 使用select_related和prefetch_related优化查询
    posts = Post.objects.filter(is_active=True).select_related(
        'author', 'category'
    ).prefetch_related(
        'tags', 'likes', 'comments'
    ).annotate(
        likes_count=Count('likes'),
        comments_count=Count('comments')
    )
    
    # 搜索功能
    query = request.GET.get('q')
    if query:
        posts = posts.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()
    
    # 分类筛选
    category_id = request.GET.get('category')
    if category_id:
        posts = posts.filter(category_id=category_id)
    
    # 分页 - 添加排序以避免警告
    posts = posts.order_by('-created_at')
    page_obj = get_paginated_queryset(posts, request, 10)

    # 使用工具函数获取缓存数据
    categories = get_cached_data(
        'home_categories',
        lambda: Category.objects.all(),
        300
    )
    
    popular_tags = get_cached_data(
        'home_popular_tags',
        lambda: Tag.objects.order_by('-posts_count')[:10],
        300
    )

    # 热门帖子（按点赞和评论数排序）
    popular_posts = posts.annotate(
        like_count=Count('likes'),
        comment_count=Count('comments')
    ).order_by('-like_count', '-comment_count')[:5]
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'popular_tags': popular_tags,
        'popular_posts': popular_posts,
        'query': query,
        'category_id': category_id,
    }
    return render(request, 'community/home.html', context)

def post_detail(request, pk):
    """帖子详情视图"""
    # 使用select_related优化查询
    post = get_object_or_404(
        Post.objects.select_related('author', 'category')
        .prefetch_related('tags', 'likes', 'comments__author', 'comments__replies__author'),
        pk=pk
    )
    
    # 使用工具函数更新浏览次数
    update_post_views(pk)
    
    # 处理评论提交
    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            
            # 创建通知
            if post.author != request.user:
                create_notification(
                    sender=request.user,
                    recipient=post.author,
                    notification_type='comment',
                    message=f'{request.user.username} 评论了你的帖子 "{post.title}"',
                    post=post,
                    comment=comment
                )
            
            messages.success(request, '评论发表成功！')
            return redirect('post_detail', pk=pk)
    else:
        comment_form = CommentForm()
    
    # 获取评论并分页
    comments = post.comments.filter(parent=None).select_related('author').prefetch_related('replies__author')
    comment_page_obj = get_paginated_queryset(comments, request, 10)
    
    context = {
        'post': post,
        'comments': comment_page_obj,
        'comment_form': comment_form,
        'is_liked': post.is_liked_by(request.user) if request.user.is_authenticated else False,
    }
    return render(request, 'community/post_detail.html', context)

@login_required
def post_create(request):
    """创建帖子"""
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            form.save_m2m()  # 保存多对多关系（标签）
            
            # 记录活动
            record_user_activity(request.user, 'post', post.id, 'post')
            
            messages.success(request, '帖子发布成功！')
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()
    
    return render(request, 'community/post_form.html', {'form': form, 'title': '发布新帖子'})

@login_required
@author_required
def post_edit(request, pk):
    """编辑帖子"""
    post = get_object_or_404(Post, pk=pk)

    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, '帖子更新成功！')
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    
    return render(request, 'community/post_form.html', {'form': form, 'title': '编辑帖子'})

@login_required
@author_required
def post_delete(request, pk):
    """删除帖子"""
    post = get_object_or_404(Post, pk=pk)

    # 检查删除时限（5分钟内）
    if not can_delete_within_time_limit(post.created_at, 5):
        messages.error(request, '帖子发布超过5分钟，无法删除')
        return redirect('post_detail', pk=post.pk)

    if request.method == 'POST':
        post.delete()
        messages.success(request, '帖子删除成功！')
        return redirect('home')

    return render(request, 'community/post_confirm_delete.html', {'post': post})

@login_required
@author_required
def comment_delete(request, pk):
    """删除评论"""
    comment = get_object_or_404(Comment, pk=pk)
    post_pk = comment.post.pk
    comment.delete()
    messages.success(request, '评论删除成功！')
    return redirect('post_detail', pk=post_pk)

def user_profile(request, username):
    """用户资料页面"""
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=user)
    comments = Comment.objects.filter(author=user)
    
    # 获取或创建用户资料
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    context = {
        'profile_user': user,
        'profile': profile,
        'posts': posts,
        'comments': comments,
    }
    return render(request, 'community/user_profile.html', context)

@login_required
def profile_edit(request):
    """编辑用户资料"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, '资料更新成功！')
            return redirect('user_profile', username=request.user.username)
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'community/profile_edit.html', {'form': form})

def register(request):
    """用户注册"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '注册成功！欢迎加入我们！')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'community/register.html', {'form': form})

def user_login(request):
    """用户登录"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'欢迎回来，{username}！')
                # 获取next参数，如果没有则跳转到论坛首页
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, '用户名或密码错误，请重试。')
        else:
            messages.error(request, '请检查输入信息是否正确。')
    else:
        form = AuthenticationForm()
    
    return render(request, 'community/login.html', {'form': form})

def category_posts(request, pk):
    """分类帖子列表"""
    category = get_object_or_404(Category, pk=pk)
    posts = Post.objects.filter(category=category)
    page_obj = get_paginated_queryset(posts, request, 10)
    
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'community/category_posts.html', context)

@login_required
def like_post(request, pk):
    """点赞/取消点赞帖子"""
    post = get_object_or_404(Post, pk=pk)
    
    if request.method == 'POST':
        like, created = Like.objects.get_or_create(user=request.user, post=post)
        
        if not created:
            # 如果已经点赞，则取消点赞
            like.delete()
            messages.success(request, '已取消点赞')
        else:
            # 创建点赞通知
            if post.author != request.user:
                create_notification(
                    sender=request.user,
                    recipient=post.author,
                    notification_type='like',
                    message=f'{request.user.username} 点赞了你的帖子 "{post.title}"',
                    post=post
                )
            messages.success(request, '点赞成功！')
        
        # 如果是AJAX请求，返回JSON响应
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'liked': post.is_liked_by(request.user),
                'likes_count': post.get_likes_count()
            })
        
        return redirect('post_detail', pk=pk)
    
    return redirect('post_detail', pk=pk)



@login_required
def notifications(request):
    """通知列表"""
    notifications_list = request.user.notifications.all()
    
    # 标记所有通知为已读
    if request.method == 'POST':
        notifications_list.update(is_read=True)
        messages.success(request, '已标记所有通知为已读')
        return redirect('notifications')
    
    page_obj = get_paginated_queryset(notifications_list, request, 20)
    
    return render(request, 'community/notifications.html', {
        'page_obj': page_obj,
        'unread_count': request.user.notifications.filter(is_read=False).count()
    })

@login_required
def mark_notification_read(request, pk):
    """标记通知为已读"""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notifications')

@login_required
@staff_required
def toggle_pin_post(request, pk):
    """切换帖子置顶状态（仅管理员）"""
    post = get_object_or_404(Post, pk=pk)
    post.is_pinned = not post.is_pinned
    post.save()
    
    action = "置顶" if post.is_pinned else "取消置顶"
    messages.success(request, f'帖子已{action}！')
    return redirect('post_detail', pk=pk)

@login_required
def report_post(request, pk):
    """举报帖子"""
    post = get_object_or_404(Post, pk=pk)
    
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.post = post
            report.save()
            messages.success(request, '举报已提交，我们会尽快处理！')
            return redirect('post_detail', pk=pk)
    else:
        form = ReportForm()
    
    return render(request, 'community/report_form.html', {
        'form': form,
        'post': post,
        'title': '举报帖子'
    })

@login_required
def report_comment(request, pk):
    """举报评论"""
    comment = get_object_or_404(Comment, pk=pk)
    
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.comment = comment
            report.save()
            messages.success(request, '举报已提交，我们会尽快处理！')
            return redirect('post_detail', pk=comment.post.pk)
    else:
        form = ReportForm()
    
    return render(request, 'community/report_form.html', {
        'form': form,
        'comment': comment,
        'title': '举报评论'
    })

@login_required
def messages_list(request):
    """私信列表"""
    received_messages = request.user.received_messages.all()
    sent_messages = request.user.sent_messages.all()
    
    # 标记消息为已读
    unread_messages = received_messages.filter(is_read=False)
    unread_messages.update(is_read=True)
    
    return render(request, 'community/messages_list.html', {
        'received_messages': received_messages,
        'sent_messages': sent_messages,
    })

@login_required
def send_message(request):
    """发送私信"""
    if request.method == 'POST':
        form = MessageForm(request.POST, initial={'current_user': request.user})
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            messages.success(request, '私信发送成功！')
            return redirect('messages_list')
    else:
        form = MessageForm(initial={'current_user': request.user})
    
    return render(request, 'community/send_message.html', {
        'form': form,
        'title': '发送私信'
    })

@login_required
def message_detail(request, pk):
    """私信详情"""
    message = get_object_or_404(Message, pk=pk)
    
    # 确保用户只能查看自己发送或接收的消息
    if message.sender != request.user and message.recipient != request.user:
        return HttpResponseForbidden("您没有权限查看此消息")
    
    # 标记为已读
    if message.recipient == request.user and not message.is_read:
        message.is_read = True
        message.save()
    
    return render(request, 'community/message_detail.html', {
        'message': message,
    })

@login_required
@staff_required
def admin_reports(request):
    """管理员查看举报列表"""
    reports = Report.objects.all()
    return render(request, 'community/admin_reports.html', {
        'reports': reports,
    })

@login_required
@staff_required
def resolve_report(request, pk):
    """处理举报"""
    report = get_object_or_404(Report, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('admin_notes', '')
        
        if action == 'resolve':
            report.status = 'resolved'
        elif action == 'dismiss':
            report.status = 'dismissed'
        
        report.admin_notes = notes
        report.resolved_by = request.user
        report.resolved_at = timezone.now()
        report.save()
        
        messages.success(request, '举报处理完成！')
        return redirect('admin_reports')
    
    return render(request, 'community/resolve_report.html', {
        'report': report,
    })

@login_required
def follow_user(request, username):
    """关注/取消关注用户"""
    user_to_follow = get_object_or_404(User, username=username)
    
    if user_to_follow == request.user:
        messages.error(request, '不能关注自己')
        return redirect('user_profile', username=username)
    
    if request.method == 'POST':
        follow, created = Follow.objects.get_or_create(follower=request.user, following=user_to_follow)
        
        if not created:
            # 如果已经关注，则取消关注
            follow.delete()
            messages.success(request, f'已取消关注 {user_to_follow.username}')
            
            # 记录活动
            record_user_activity(request.user, 'unfollow', user_to_follow.id, 'user')
        else:
            # 创建关注通知
            create_notification(
                sender=request.user,
                recipient=user_to_follow,
                notification_type='follow',
                message=f'{request.user.username} 关注了你',
            )
            messages.success(request, f'已关注 {user_to_follow.username}')
            
            # 记录活动
            record_user_activity(request.user, 'follow', user_to_follow.id, 'user')
    
    return redirect('user_profile', username=username)

@login_required
def tag_posts(request, pk):
    """标签下的帖子列表"""
    tag = get_object_or_404(Tag, pk=pk)
    posts = Post.objects.filter(tags=tag, is_active=True)
    page_obj = get_paginated_queryset(posts, request, 10)
    
    context = {
        'tag': tag,
        'page_obj': page_obj,
    }
    return render(request, 'community/tag_posts.html', context)

@login_required
def tag_list(request):
    """标签列表"""
    tags = Tag.objects.order_by('-posts_count')
    
    context = {
        'tags': tags,
    }
    return render(request, 'community/tag_list.html', context)

@login_required
@staff_required
def create_tag(request):
    """创建标签"""
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            tag = form.save()
            messages.success(request, '标签创建成功！')
            return redirect('tag_list')
    else:
        form = TagForm()
    
    return render(request, 'community/tag_form.html', {
        'form': form,
        'title': '创建标签'
    })



@login_required
@staff_required
def admin_delete_post(request, pk):
    """管理员删除帖子"""
    post = get_object_or_404(Post, pk=pk)
    
    if request.method == 'POST':
        form = DeletePostForm(request.POST)
        if form.is_valid():
            post.is_active = False
            post.deleted_at = timezone.now()
            post.deleted_by = request.user
            post.delete_reason = form.cleaned_data['delete_reason']
            post.save()
            
            # 创建通知
            create_notification(
                sender=request.user,
                recipient=post.author,
                notification_type='comment',
                message=f'您的帖子 "{post.title}" 已被管理员删除，原因：{post.delete_reason}',
                post=post
            )
            
            messages.success(request, '帖子删除成功！')
            return redirect('home')
    else:
        form = DeletePostForm()
    
    return render(request, 'community/admin_delete_post.html', {
        'form': form,
        'post': post,
    })

@login_required
@staff_required
def admin_delete_comment(request, pk):
    """管理员删除评论"""
    comment = get_object_or_404(Comment, pk=pk)
    
    if request.method == 'POST':
        form = DeleteCommentForm(request.POST)
        if form.is_valid():
            comment.is_active = False
            comment.deleted_at = timezone.now()
            comment.deleted_by = request.user
            comment.delete_reason = form.cleaned_data['delete_reason']
            comment.save()
            
            # 创建通知
            create_notification(
                sender=request.user,
                recipient=comment.author,
                notification_type='comment',
                message=f'您的评论已被管理员删除，原因：{comment.delete_reason}',
                comment=comment
            )
            
            messages.success(request, '评论删除成功！')
            return redirect('post_detail', pk=comment.post.pk)
    else:
        form = DeleteCommentForm()
    
    return render(request, 'community/admin_delete_comment.html', {
        'form': form,
        'comment': comment,
    })

@login_required
@staff_required
def admin_ban_user(request, username):
    """管理员封禁用户"""
    user = get_object_or_404(User, username=username)
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        form = BanUserForm(request.POST)
        if form.is_valid():
            profile.is_banned = True
            profile.banned_at = timezone.now()
            profile.banned_by = request.user
            profile.ban_reason = form.cleaned_data['ban_reason']
            profile.ban_expires_at = form.get_ban_expires_at()
            profile.save()
            
            # 创建通知
            ban_type = form.cleaned_data['ban_type']
            ban_duration = form.cleaned_data.get('ban_duration', '')
            ban_message = f'您的账号已被{ban_type}'
            if ban_duration:
                ban_message += f'，时长：{ban_duration}天'
            ban_message += f'，原因：{profile.ban_reason}'
            
            create_notification(
                sender=request.user,
                recipient=user,
                notification_type='comment',
                message=ban_message
            )
            
            messages.success(request, f'用户 {user.username} 封禁成功！')
            return redirect('user_profile', username=username)
    else:
        form = BanUserForm()
    
    return render(request, 'community/admin_ban_user.html', {
        'form': form,
        'profile_user': user,
        'profile': profile,
    })

@login_required
@staff_required
def admin_unban_user(request, username):
    """管理员解封用户"""
    user = get_object_or_404(User, username=username)
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        form = UnbanUserForm(request.POST)
        if form.is_valid():
            profile.is_banned = False
            profile.ban_expires_at = None
            profile.ban_reason = ''
            profile.save()
            
            # 创建通知
            unban_message = '您的账号已被解封'
            if form.cleaned_data.get('unban_reason'):
                unban_message += f'，原因：{form.cleaned_data["unban_reason"]}'
            
            create_notification(
                sender=request.user,
                recipient=user,
                notification_type='comment',
                message=unban_message
            )
            
            messages.success(request, f'用户 {user.username} 解封成功！')
            return redirect('user_profile', username=username)
    else:
        form = UnbanUserForm()
    
    return render(request, 'community/admin_unban_user.html', {
        'form': form,
        'profile_user': user,
        'profile': profile,
    })

@login_required
@staff_required
def statistics(request):
    """网站统计页面"""
    # 基础统计
    total_users = User.objects.count()
    total_posts = Post.objects.filter(is_active=True).count()
    total_comments = Comment.objects.count()
    total_views = Post.objects.aggregate(total_views=Sum('views'))['total_views'] or 0
    
    # 今日统计
    today = timezone.now().date()
    today_users = User.objects.filter(date_joined__date=today).count()
    today_posts = Post.objects.filter(created_at__date=today).count()
    today_comments = Comment.objects.filter(created_at__date=today).count()
    
    # 热门标签
    popular_tags = Tag.objects.order_by('-posts_count')[:10]
    
    # 活跃用户
    active_users = User.objects.annotate(
        posts_count=Count('post'),
        comments_count=Count('comment')
    ).order_by('-posts_count', '-comments_count')[:10]
    
    context = {
        'total_users': total_users,
        'total_posts': total_posts,
        'total_comments': total_comments,
        'total_views': total_views,
        'today_users': today_users,
        'today_posts': today_posts,
        'today_comments': today_comments,
        'popular_tags': popular_tags,
        'active_users': active_users,
    }
    return render(request, 'community/statistics.html', context)

@login_required
def user_activity(request, username):
    """用户活动页面"""
    user = get_object_or_404(User, username=username)
    activities = user.activities.all()
    page_obj = get_paginated_queryset(activities, request, 20)
    
    context = {
        'profile_user': user,
        'page_obj': page_obj,
    }
    return render(request, 'community/user_activity.html', context)

@login_required
def advanced_search(request):
    """高级搜索"""
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'all')
    category_id = request.GET.get('category', '')
    author = request.GET.get('author', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    sort_by = request.GET.get('sort', 'relevance')
    
    if query:
        # 使用Django ORM进行搜索
        posts = Post.objects.filter(is_active=True)
        
        # 按类型筛选
        if search_type == 'posts':
            posts = posts.filter(
                Q(title__icontains=query) | 
                Q(content__icontains=query)
            )
        elif search_type == 'categories':
            posts = posts.filter(category__name__icontains=query)
        elif search_type == 'tags':
            posts = posts.filter(tags__name__icontains=query)
        else:
            # 全部搜索
            posts = posts.filter(
                Q(title__icontains=query) | 
                Q(content__icontains=query) |
                Q(category__name__icontains=query) |
                Q(tags__name__icontains=query)
            ).distinct()
        
        # 按分类筛选
        if category_id:
            posts = posts.filter(category_id=category_id)
        
        # 按作者筛选
        if author:
            posts = posts.filter(author__username__icontains=author)
        
        # 按日期筛选
        if date_from:
            posts = posts.filter(created_at__gte=date_from)
        if date_to:
            posts = posts.filter(created_at__lte=date_to)
        
        # 排序
        if sort_by == 'date':
            posts = posts.order_by('-created_at')
        elif sort_by == 'views':
            posts = posts.order_by('-views')
        elif sort_by == 'likes':
            posts = posts.annotate(likes_count=Count('likes')).order_by('-likes_count')
        elif sort_by == 'comments':
            posts = posts.annotate(comments_count=Count('comments')).order_by('-comments_count')
        else:
            # 默认按创建时间排序
            posts = posts.order_by('-created_at')
        
        # 分页
        page_obj = get_paginated_queryset(posts, request, 10)
    else:
        page_obj = None
    
    # 获取筛选选项
    categories = Category.objects.all()
    
    context = {
        'query': query,
        'search_type': search_type,
        'category_id': category_id,
        'author': author,
        'date_from': date_from,
        'date_to': date_to,
        'sort_by': sort_by,
        'page_obj': page_obj,
        'categories': categories,
    }
    
    return render(request, 'community/advanced_search.html', context)
