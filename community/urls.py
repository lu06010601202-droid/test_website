from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    # 欢迎页面
    path('', views.welcome, name='welcome'),
    
    # 论坛相关
    path('forum/', views.home, name='home'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/create/', views.post_create, name='post_create'),
    path('post/<int:pk>/edit/', views.post_edit, name='post_edit'),
    path('post/<int:pk>/delete/', views.post_delete, name='post_delete'),
    path('post/<int:pk>/pin/', views.toggle_pin_post, name='toggle_pin_post'),
    
    # 评论相关
    path('comment/<int:pk>/delete/', views.comment_delete, name='comment_delete'),
    
    # 举报相关
    path('post/<int:pk>/report/', views.report_post, name='report_post'),
    path('comment/<int:pk>/report/', views.report_comment, name='report_comment'),
    
    # 私信相关
    path('messages/', views.messages_list, name='messages_list'),
    path('messages/send/', views.send_message, name='send_message'),
    path('messages/<int:pk>/', views.message_detail, name='message_detail'),
    
    # 用户认证
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    
    # 用户资料
    path('user/<str:username>/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    
    # 分类
    path('category/<int:pk>/', views.category_posts, name='category_posts'),
    path('post/<int:pk>/like/', views.like_post, name='like_post'),
    
    # 通知
    path('notifications/', views.notifications, name='notifications'),
    path('notification/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    # 关注功能
    path('user/<str:username>/follow/', views.follow_user, name='follow_user'),
    
    # 标签功能
    path('tags/', views.tag_list, name='tag_list'),
    path('tags/create/', views.create_tag, name='create_tag'),
    path('tag/<int:pk>/', views.tag_posts, name='tag_posts'),
    
    # 管理员功能
    path('admin/post/<int:pk>/delete/', views.admin_delete_post, name='admin_delete_post'),
    path('admin/comment/<int:pk>/delete/', views.admin_delete_comment, name='admin_delete_comment'),
    path('admin/user/<str:username>/ban/', views.admin_ban_user, name='admin_ban_user'),
    path('admin/user/<str:username>/unban/', views.admin_unban_user, name='admin_unban_user'),
    
    # 统计功能
    path('admin/statistics/', views.statistics, name='statistics'),
    path('user/<str:username>/activity/', views.user_activity, name='user_activity'),
    
    # 管理员功能
    path('admin/reports/', views.admin_reports, name='admin_reports'),
    path('admin/reports/<int:pk>/resolve/', views.resolve_report, name='resolve_report'),
    
    # 高级搜索
    path('search/', views.advanced_search, name='advanced_search'),
] 