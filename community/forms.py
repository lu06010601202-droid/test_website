from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Post, Comment, UserProfile, Report, Message, Follow, Tag

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'category', 'tags', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入帖子标题'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '多个标签用逗号分隔'}),
        }
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title.strip()) < 5:
            raise forms.ValidationError('标题至少需要5个字符')
        return title.strip()
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content.strip()) < 10:
            raise forms.ValidationError('内容至少需要10个字符')
        return content

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入评论内容'}),
        }
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content.strip()) < 2:
            raise forms.ValidationError('评论内容至少需要2个字符')
        return content.strip()

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio', 'website', 'location']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'}) 

class ReportForm(forms.ModelForm):
    """举报表单"""
    class Meta:
        model = Report
        fields = ['report_type', 'reason']
        widgets = {
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '请详细描述举报原因...'}),
        }

class MessageForm(forms.ModelForm):
    """私信表单"""
    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'content']
        widgets = {
            'recipient': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入主题...'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '请输入消息内容...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 只显示非当前用户的其他用户
        if 'initial' in kwargs and 'current_user' in kwargs['initial']:
            current_user = kwargs['initial']['current_user']
            self.fields['recipient'].queryset = User.objects.exclude(id=current_user.id) 

class FollowForm(forms.ModelForm):
    """关注表单"""
    class Meta:
        model = Follow
        fields = []

class TagForm(forms.ModelForm):
    """标签表单"""
    class Meta:
        model = Tag
        fields = ['name', 'description', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入标签名称...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入标签描述...'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }

 