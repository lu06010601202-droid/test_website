from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django_ckeditor_5.fields import CKEditor5Field
from .utils.validators import validate_file_size, validate_file_extension, validate_image_extension, validate_file_content

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='分类名称')
    description = models.TextField(blank=True, verbose_name='分类描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '分类'
        verbose_name_plural = '分类'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_posts', kwargs={'pk': self.pk})

class Tag(models.Model):
    """标签模型"""
    name = models.CharField(max_length=50, unique=True, verbose_name='标签名称')
    description = models.TextField(blank=True, verbose_name='标签描述')
    color = models.CharField(max_length=7, default='#007bff', verbose_name='标签颜色')
    posts_count = models.PositiveIntegerField(default=0, verbose_name='使用次数')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '标签'
        verbose_name_plural = '标签'
        ordering = ['-posts_count', 'name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('tag_posts', kwargs={'pk': self.pk})
    
    def update_posts_count(self):
        """更新使用次数"""
        from django.db.models import Count
        count = self.post_set.aggregate(count=Count('id'))['count']
        self.posts_count = count
        self.save(update_fields=['posts_count'])
    
    def get_popularity_level(self):
        """获取热门程度等级"""
        if self.posts_count >= 100:
            return '非常热门'
        elif self.posts_count >= 50:
            return '热门'
        elif self.posts_count >= 20:
            return '较热门'
        elif self.posts_count >= 10:
            return '一般'
        else:
            return '冷门'

class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name='标题')
    content = CKEditor5Field('内容', config_name='extends')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='作者')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='分类')
    tags = models.ManyToManyField(Tag, blank=True, verbose_name='标签')
    attachment = models.FileField(
        upload_to='post_attachments/', 
        null=True, 
        blank=True, 
        verbose_name='附件',
        validators=[validate_file_size, validate_file_extension, validate_file_content]
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    views = models.PositiveIntegerField(default=0, verbose_name='浏览次数')
    is_pinned = models.BooleanField(default=False, verbose_name='是否置顶')
    
    # 状态字段
    is_active = models.BooleanField(default=True, verbose_name='是否有效')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='删除时间')
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_posts', verbose_name='删除人')
    delete_reason = models.TextField(blank=True, verbose_name='删除原因')

    class Meta:
        verbose_name = '帖子'
        verbose_name_plural = '帖子'
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'pk': self.pk})

    def increase_views(self):
        self.views += 1
        self.save(update_fields=['views'])
    
    def get_likes_count(self):
        """获取点赞数量"""
        return self.likes.count()
    
    def is_liked_by(self, user):
        """检查用户是否已点赞"""
        if not user.is_authenticated:
            return False
        return self.likes.filter(user=user).exists()
    
    def get_tags_display(self):
        """获取标签显示字符串"""
        return ', '.join([tag.name for tag in self.tags.all()])
    
    def is_deleted(self):
        """检查帖子是否已被删除"""
        return not self.is_active
    
    def can_be_viewed_by(self, user):
        """检查用户是否可以查看此帖子"""
        if not self.is_active:
            return user.is_authenticated and user.is_staff
        return True
    
    def get_comment_count(self):
        """获取评论数量"""
        return self.comments.count()
    
    def get_reply_count(self):
        """获取回复数量"""
        return Comment.objects.filter(parent__post=self).count()
    
    def get_total_comment_count(self):
        """获取总评论数（包括回复）"""
        return self.get_comment_count() + self.get_reply_count()
    
    def get_engagement_score(self):
        """获取互动分数（点赞数 + 评论数）"""
        return self.get_likes_count() + self.get_total_comment_count()
    
    def is_trending(self):
        """检查是否为热门帖子（简单判断：点赞数>10或评论数>5）"""
        return self.get_likes_count() > 10 or self.get_total_comment_count() > 5

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='帖子')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='作者')
    content = models.TextField(verbose_name='评论内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies', verbose_name='父评论')
    
    # 删除相关字段
    is_active = models.BooleanField(default=True, verbose_name='是否有效')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='删除时间')
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_comments', verbose_name='删除人')
    delete_reason = models.TextField(blank=True, verbose_name='删除原因')

    class Meta:
        verbose_name = '评论'
        verbose_name_plural = '评论'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author.username} 评论于 {self.post.title}'
    
    def is_reply(self):
        """检查是否为回复"""
        return self.parent is not None
    
    def get_reply_count(self):
        """获取回复数量"""
        return self.replies.count()
    
    def get_content_preview(self, max_length=50):
        """获取内容预览"""
        content = self.content.strip()
        if len(content) <= max_length:
            return content
        return content[:max_length] + '...'
    
    def is_deleted(self):
        """检查评论是否已被删除"""
        return not self.is_active
    
    def can_be_viewed_by(self, user):
        """检查用户是否可以查看此评论"""
        if not self.is_active:
            return user.is_authenticated and user.is_staff
        return True

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='用户')
    avatar = models.ImageField(
        upload_to='avatars/', 
        null=True, 
        blank=True, 
        verbose_name='头像',
        validators=[validate_file_size, validate_image_extension, validate_file_content]
    )
    bio = models.TextField(max_length=500, blank=True, verbose_name='个人简介')
    website = models.URLField(blank=True, verbose_name='个人网站')
    location = models.CharField(max_length=100, blank=True, verbose_name='所在地')
    join_date = models.DateTimeField(auto_now_add=True, verbose_name='加入时间')
    
    # 用户等级和权限
    LEVEL_CHOICES = [
        (1, '新手'),
        (2, '初级用户'),
        (3, '中级用户'),
        (4, '高级用户'),
        (5, '专家'),
    ]
    level = models.IntegerField(choices=LEVEL_CHOICES, default=1, verbose_name='用户等级')
    experience_points = models.PositiveIntegerField(default=0, verbose_name='经验值')
    
    # 封禁相关字段
    is_banned = models.BooleanField(default=False, verbose_name='是否被封禁')
    banned_at = models.DateTimeField(null=True, blank=True, verbose_name='封禁时间')
    banned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='banned_users', verbose_name='封禁人')
    ban_reason = models.TextField(blank=True, verbose_name='封禁原因')
    ban_expires_at = models.DateTimeField(null=True, blank=True, verbose_name='封禁到期时间')

    class Meta:
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'

    def __str__(self):
        return self.user.username

    def get_absolute_url(self):
        return reverse('user_profile', kwargs={'username': self.user.username})
    
    def get_post_count(self):
        """获取用户发帖数量"""
        return self.user.post_set.count()
    
    def get_comment_count(self):
        """获取用户评论数量"""
        return self.user.comment_set.count()
    
    def get_follower_count(self):
        """获取用户粉丝数量"""
        return self.user.followers.count()
    
    def get_following_count(self):
        """获取用户关注数量"""
        return self.user.following.count()
    
    def is_permanently_banned(self):
        """检查用户是否被永久封禁"""
        return self.is_banned and self.ban_expires_at is None
    
    def is_temporarily_banned(self):
        """检查用户是否被临时封禁"""
        if not self.is_banned or self.ban_expires_at is None:
            return False
        from django.utils import timezone
        return timezone.now() < self.ban_expires_at
    
    def is_currently_banned(self):
        """检查用户当前是否被封禁"""
        if not self.is_banned:
            return False
        if self.ban_expires_at is None:  # 永久封禁
            return True
        from django.utils import timezone
        return timezone.now() < self.ban_expires_at
    
    def get_ban_status_display(self):
        """获取封禁状态显示"""
        if not self.is_banned:
            return '正常'
        if self.ban_expires_at is None:
            return '永久封禁'
        from django.utils import timezone
        if timezone.now() < self.ban_expires_at:
            return f'临时封禁 (到期时间: {self.ban_expires_at.strftime("%Y-%m-%d %H:%M")})'
        else:
            return '封禁已过期'
    
    def get_level_display_name(self):
        """获取等级显示名称"""
        return dict(self.LEVEL_CHOICES).get(self.level, '未知')
    
    def get_experience_progress(self):
        """获取经验值进度百分比"""
        # 简单的经验值计算，每级需要1000经验
        current_level_exp = (self.level - 1) * 1000
        next_level_exp = self.level * 1000
        progress = ((self.experience_points - current_level_exp) / 
                   (next_level_exp - current_level_exp)) * 100
        return min(100, max(0, progress))

class Like(models.Model):
    """点赞模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes', verbose_name='帖子')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='点赞时间')

    class Meta:
        verbose_name = '点赞'
        verbose_name_plural = '点赞'
        unique_together = ['user', 'post']  # 防止重复点赞
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} 点赞了 {self.post.title}'

class Notification(models.Model):
    """通知模型"""
    NOTIFICATION_TYPES = [
        ('comment', '评论'),
        ('like', '点赞'),
        ('follow', '关注'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name='接收者')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', verbose_name='发送者')
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, verbose_name='通知类型')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, verbose_name='相关帖子')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, verbose_name='相关评论')
    message = models.TextField(verbose_name='通知内容')
    is_read = models.BooleanField(default=False, verbose_name='是否已读')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '通知'
        verbose_name_plural = '通知'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.sender.username} -> {self.recipient.username}: {self.message}'
    
    def get_type_display_name(self):
        """获取通知类型显示名称"""
        return dict(self.NOTIFICATION_TYPES).get(self.notification_type, '未知')
    
    def get_icon_class(self):
        """获取通知图标CSS类"""
        icon_map = {
            'comment': 'fas fa-comment',
            'like': 'fas fa-heart',
            'follow': 'fas fa-user-plus',
        }
        return icon_map.get(self.notification_type, 'fas fa-bell')
    
    def get_time_ago(self):
        """获取相对时间"""
        from django.utils import timezone
        now = timezone.now()
        diff = now - self.created_at
        
        if diff.days > 0:
            return f'{diff.days}天前'
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f'{hours}小时前'
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f'{minutes}分钟前'
        else:
            return '刚刚'

class Message(models.Model):
    """私信模型"""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', verbose_name='发送者')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', verbose_name='接收者')
    subject = models.CharField(max_length=200, verbose_name='主题')
    content = models.TextField(verbose_name='内容')
    is_read = models.BooleanField(default=False, verbose_name='是否已读')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='发送时间')
    
    class Meta:
        verbose_name = '私信'
        verbose_name_plural = '私信'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.sender.username} -> {self.recipient.username}: {self.subject}'
    
    def get_content_preview(self, max_length=100):
        """获取内容预览"""
        content = self.content.strip()
        if len(content) <= max_length:
            return content
        return content[:max_length] + '...'
    
    def get_time_ago(self):
        """获取相对时间"""
        from django.utils import timezone
        now = timezone.now()
        diff = now - self.created_at
        
        if diff.days > 0:
            return f'{diff.days}天前'
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f'{hours}小时前'
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f'{minutes}分钟前'
        else:
            return '刚刚'

class Follow(models.Model):
    """用户关注模型"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following', verbose_name='关注者')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers', verbose_name='被关注者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='关注时间')
    
    class Meta:
        verbose_name = '关注关系'
        verbose_name_plural = '关注关系'
        unique_together = ['follower', 'following']  # 防止重复关注
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.follower.username} 关注了 {self.following.username}'

class Report(models.Model):
    """举报模型"""
    REPORT_TYPES = [
        ('spam', '垃圾信息'),
        ('inappropriate', '不当内容'),
        ('harassment', '骚扰行为'),
        ('copyright', '版权侵犯'),
        ('other', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('reviewed', '已审核'),
        ('resolved', '已解决'),
        ('dismissed', '已驳回'),
    ]
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports', verbose_name='举报者')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name='reports', verbose_name='被举报帖子')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='reports', verbose_name='被举报评论')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, verbose_name='举报类型')
    reason = models.TextField(verbose_name='举报原因')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name='处理状态')
    admin_notes = models.TextField(blank=True, verbose_name='管理员备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='举报时间')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='处理时间')
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_reports', verbose_name='处理人')

    class Meta:
        verbose_name = '举报'
        verbose_name_plural = '举报'
        ordering = ['-created_at']

    def __str__(self):
        target = self.post.title if self.post else f"评论 {self.comment.id}"
        return f'{self.reporter.username} 举报了 {target}'

    def get_target(self):
        """获取被举报的目标"""
        return self.post or self.comment
    
    def get_type_display_name(self):
        """获取举报类型显示名称"""
        return dict(self.REPORT_TYPES).get(self.report_type, '未知')
    
    def get_status_display_name(self):
        """获取状态显示名称"""
        return dict(self.STATUS_CHOICES).get(self.status, '未知')
    
    def is_pending(self):
        """检查是否为待处理状态"""
        return self.status == 'pending'
    
    def is_resolved(self):
        """检查是否已处理"""
        return self.status in ['resolved', 'dismissed']
    
    def get_time_ago(self):
        """获取相对时间"""
        from django.utils import timezone
        now = timezone.now()
        diff = now - self.created_at
        
        if diff.days > 0:
            return f'{diff.days}天前'
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f'{hours}小时前'
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f'{minutes}分钟前'
        else:
            return '刚刚'

class UserActivity(models.Model):
    """用户活动统计模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities', verbose_name='用户')
    activity_type = models.CharField(max_length=20, verbose_name='活动类型')  # post, comment, like, follow
    target_id = models.PositiveIntegerField(verbose_name='目标ID')
    target_type = models.CharField(max_length=20, verbose_name='目标类型')  # post, comment, user
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='活动时间')
    
    class Meta:
        verbose_name = '用户活动'
        verbose_name_plural = '用户活动'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.user.username} - {self.activity_type}'
    
    def get_activity_display_name(self):
        """获取活动类型显示名称"""
        activity_names = {
            'post': '发布帖子',
            'comment': '发表评论',
            'like': '点赞',
            'follow': '关注用户',
            'unfollow': '取消关注',
        }
        return activity_names.get(self.activity_type, self.activity_type)
    
    def get_target_display_name(self):
        """获取目标类型显示名称"""
        target_names = {
            'post': '帖子',
            'comment': '评论',
            'user': '用户',
        }
        return target_names.get(self.target_type, self.target_type)

class SiteStatistics(models.Model):
    """网站统计模型"""
    date = models.DateField(unique=True, verbose_name='日期')
    total_users = models.PositiveIntegerField(default=0, verbose_name='总用户数')
    total_posts = models.PositiveIntegerField(default=0, verbose_name='总帖子数')
    total_comments = models.PositiveIntegerField(default=0, verbose_name='总评论数')
    total_views = models.PositiveIntegerField(default=0, verbose_name='总浏览量')
    new_users = models.PositiveIntegerField(default=0, verbose_name='新增用户数')
    new_posts = models.PositiveIntegerField(default=0, verbose_name='新增帖子数')
    new_comments = models.PositiveIntegerField(default=0, verbose_name='新增评论数')
    
    class Meta:
        verbose_name = '网站统计'
        verbose_name_plural = '网站统计'
        ordering = ['-date']
    
    def __str__(self):
        return f'{self.date} - 统计'
    
    def get_growth_rate(self, field_name):
        """获取增长率"""
        if self.date.day == 1:  # 月初，无法计算增长率
            return 0
        
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            yesterday = self.date - timedelta(days=1)
            yesterday_stats = SiteStatistics.objects.get(date=yesterday)
            
            current_value = getattr(self, field_name)
            previous_value = getattr(yesterday_stats, field_name)
            
            if previous_value == 0:
                return 100 if current_value > 0 else 0
            
            return round(((current_value - previous_value) / previous_value) * 100, 2)
        except SiteStatistics.DoesNotExist:
            return 0
    
    def get_total_engagement(self):
        """获取总互动数（帖子数 + 评论数）"""
        return self.total_posts + self.total_comments
