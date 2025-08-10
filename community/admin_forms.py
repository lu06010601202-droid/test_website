from django import forms
from django.utils import timezone
from datetime import timedelta

class DeletePostForm(forms.Form):
    """删除帖子表单"""
    delete_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '请输入删除原因...'
        }),
        max_length=500,
        required=True,
        label='删除原因'
    )

class DeleteCommentForm(forms.Form):
    """删除评论表单"""
    delete_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '请输入删除原因...'
        }),
        max_length=500,
        required=True,
        label='删除原因'
    )

class BanUserForm(forms.Form):
    """封禁用户表单"""
    BAN_TYPE_CHOICES = [
        ('temporary', '临时封禁'),
        ('permanent', '永久封禁'),
    ]
    
    ban_type = forms.ChoiceField(
        choices=BAN_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='封禁类型'
    )
    
    ban_duration = forms.ChoiceField(
        choices=[
            (1, '1天'),
            (3, '3天'),
            (7, '1周'),
            (30, '1个月'),
            (90, '3个月'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label='封禁时长'
    )
    
    ban_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '请输入封禁原因...'
        }),
        max_length=500,
        required=True,
        label='封禁原因'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        ban_type = cleaned_data.get('ban_type')
        ban_duration = cleaned_data.get('ban_duration')
        
        if ban_type == 'temporary' and not ban_duration:
            raise forms.ValidationError('临时封禁必须选择封禁时长')
        
        return cleaned_data
    
    def get_ban_expires_at(self):
        """获取封禁到期时间"""
        ban_type = self.cleaned_data.get('ban_type')
        ban_duration = self.cleaned_data.get('ban_duration')
        
        if ban_type == 'permanent':
            return None
        
        if ban_duration:
            days = int(ban_duration)
            return timezone.now() + timedelta(days=days)
        
        return None

class UnbanUserForm(forms.Form):
    """解封用户表单"""
    unban_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '请输入解封原因...'
        }),
        max_length=500,
        required=False,
        label='解封原因'
    )
