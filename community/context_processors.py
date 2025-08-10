def notifications_processor(request):
    """为所有模板提供未读通知数量"""
    if request.user.is_authenticated:
        unread_count = request.user.notifications.filter(is_read=False).count()
        return {'unread_notifications_count': unread_count}
    return {'unread_notifications_count': 0} 