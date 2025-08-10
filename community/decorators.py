from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from .models import Post, Comment

def staff_required(view_func):
    """要求用户是管理员"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden("您没有权限执行此操作")
        return view_func(request, *args, **kwargs)
    return wrapper

def author_required(view_func):
    """要求用户是内容作者"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        pk = kwargs.get('pk')
        if not pk:
            return HttpResponseForbidden("参数错误")
        
        # 根据URL路径判断是帖子还是评论
        if 'comment' in request.path:
            obj = get_object_or_404(Comment, pk=pk)
        else:
            obj = get_object_or_404(Post, pk=pk)
        
        if obj.author != request.user:
            return HttpResponseForbidden("您没有权限执行此操作")
        
        return view_func(request, *args, **kwargs)
    return wrapper


