from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from ..models import Notification, UserActivity
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def get_cached_data(cache_key, queryset_func, timeout=300):
    """获取缓存数据，如果不存在则执行查询并缓存"""
    data = cache.get(cache_key)
    if data is None:
        data = queryset_func()
        cache.set(cache_key, data, timeout)
    return data

def update_post_views(post_id):
    """更新帖子浏览次数（使用缓存优化）"""
    cache_key = f'post_views_{post_id}'
    current_views = cache.get(cache_key, 0)
    current_views += 1
    cache.set(cache_key, current_views, 300)
    
    # 每10次访问才更新数据库
    if current_views % 10 == 0:
        from .models import Post
        post = Post.objects.get(id=post_id)
        post.views = current_views
        post.save(update_fields=['views'])

def create_notification(sender, recipient, notification_type, message, post=None, comment=None):
    """创建通知的辅助函数"""
    if sender != recipient:  # 不给自己发通知
        notification = Notification.objects.create(
            sender=sender,
            recipient=recipient,
            notification_type=notification_type,
            message=message,
            post=post,
            comment=comment
        )
        
        # 发送实时通知
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"notifications_{recipient.id}",
                {
                    "type": "notification_message",
                    "message": message,
                    "notification_id": notification.id,
                    "notification_type": notification_type,
                }
            )
        except Exception:
            # 如果WebSocket不可用，忽略错误
            pass
        
        return notification

def record_user_activity(user, activity_type, target_id, target_type):
    """记录用户活动"""
    UserActivity.objects.create(
        user=user,
        activity_type=activity_type,
        target_id=target_id,
        target_type=target_type
    )

def can_delete_within_time_limit(created_at, time_limit_minutes=5):
    """检查是否在删除时限内"""
    return timezone.now() - created_at <= timedelta(minutes=time_limit_minutes)

def get_paginated_queryset(queryset, request, page_size=10):
    """获取分页查询集"""
    from django.core.paginator import Paginator
    paginator = Paginator(queryset, page_size)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
