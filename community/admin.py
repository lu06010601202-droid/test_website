from django.contrib import admin
from .models import Category, Post, Comment, UserProfile, Like, Notification, Message, Report, Follow, Tag, UserActivity, SiteStatistics

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['created_at']

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'is_active', 'views', 'is_pinned', 'created_at']
    list_filter = ['category', 'is_active', 'is_pinned', 'created_at']
    search_fields = ['title', 'content', 'author__username']
    list_editable = ['is_pinned', 'is_active']
    readonly_fields = ['views', 'created_at', 'updated_at', 'deleted_at', 'deleted_by', 'delete_reason']
    actions = ['activate_posts', 'deactivate_posts', 'pin_posts', 'unpin_posts']
    
    def activate_posts(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'成功激活 {updated} 个帖子')
    activate_posts.short_description = '批量激活'
    
    def deactivate_posts(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'成功停用 {updated} 个帖子')
    deactivate_posts.short_description = '批量停用'
    
    def pin_posts(self, request, queryset):
        updated = queryset.update(is_pinned=True)
        self.message_user(request, f'成功置顶 {updated} 个帖子')
    pin_posts.short_description = '批量置顶'
    
    def unpin_posts(self, request, queryset):
        updated = queryset.update(is_pinned=False)
        self.message_user(request, f'成功取消置顶 {updated} 个帖子')
    unpin_posts.short_description = '批量取消置顶'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'content', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'post__category']
    search_fields = ['content', 'author__username', 'post__title']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'deleted_at', 'deleted_by', 'delete_reason']
    actions = ['activate_comments', 'deactivate_comments']
    
    def activate_comments(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'成功激活 {updated} 个评论')
    activate_comments.short_description = '批量激活'
    
    def deactivate_comments(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'成功停用 {updated} 个评论')
    deactivate_comments.short_description = '批量停用'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'is_banned', 'level', 'join_date']
    list_filter = ['is_banned', 'level', 'join_date']
    search_fields = ['user__username', 'bio', 'location']
    list_editable = ['is_banned', 'level']
    readonly_fields = ['join_date', 'banned_at', 'banned_by', 'ban_reason', 'ban_expires_at']
    actions = ['ban_users', 'unban_users']
    
    def ban_users(self, request, queryset):
        updated = queryset.update(is_banned=True)
        self.message_user(request, f'成功封禁 {updated} 个用户')
    ban_users.short_description = '批量封禁'
    
    def unban_users(self, request, queryset):
        updated = queryset.update(is_banned=False)
        self.message_user(request, f'成功解封 {updated} 个用户')
    unban_users.short_description = '批量解封'

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__title']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'sender', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__username', 'sender__username', 'message']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['sender__username', 'recipient__username', 'subject', 'content']

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'report_type', 'status', 'created_at']
    list_filter = ['report_type', 'status', 'created_at']
    search_fields = ['reporter__username', 'reason']
    readonly_fields = ['reporter', 'post', 'comment', 'created_at']
    actions = ['resolve_reports', 'dismiss_reports']
    
    def resolve_reports(self, request, queryset):
        updated = queryset.update(status='resolved')
        self.message_user(request, f'成功处理 {updated} 个举报')
    resolve_reports.short_description = '批量处理举报'
    
    def dismiss_reports(self, request, queryset):
        updated = queryset.update(status='dismissed')
        self.message_user(request, f'成功驳回 {updated} 个举报')
    dismiss_reports.short_description = '批量驳回举报'

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__username', 'following__username']

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'posts_count', 'color', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['posts_count']

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'target_type', 'created_at']
    list_filter = ['activity_type', 'target_type', 'created_at']
    search_fields = ['user__username']

@admin.register(SiteStatistics)
class SiteStatisticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_users', 'total_posts', 'total_comments', 'total_views']
    list_filter = ['date']
    readonly_fields = ['date']
