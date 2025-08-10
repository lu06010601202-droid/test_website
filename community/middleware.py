import time
from django.core.cache import cache
from django.http import HttpResponse
from django.conf import settings

class RateLimitMiddleware:
    """API限流中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # 只对POST请求进行限流
        if request.method == 'POST':
            client_ip = self.get_client_ip(request)
            user_id = request.user.id if request.user.is_authenticated else 'anonymous'
            
            # 创建限流键
            rate_limit_key = f"rate_limit:{client_ip}:{user_id}"
            
            # 检查是否超过限制
            if not self.check_rate_limit(rate_limit_key):
                return HttpResponse("请求过于频繁，请稍后再试。", status=429)
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """获取客户端IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def check_rate_limit(self, key, limit=10, window=60):
        """检查限流"""
        current_time = int(time.time())
        window_start = current_time - window
        
        # 获取当前时间窗口内的请求次数
        requests = cache.get(key, [])
        
        # 清理过期的请求记录
        requests = [req_time for req_time in requests if req_time > window_start]
        
        # 检查是否超过限制
        if len(requests) >= limit:
            return False
        
        # 添加当前请求
        requests.append(current_time)
        cache.set(key, requests, window)
        
        return True
