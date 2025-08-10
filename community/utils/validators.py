import os
from django.core.exceptions import ValidationError
from django.conf import settings
from django.template.defaultfilters import filesizeformat

def validate_file_size(value):
    """验证文件大小"""
    if value.size > settings.MAX_FILE_SIZE:
        raise ValidationError(
            f'文件大小不能超过 {filesizeformat(settings.MAX_FILE_SIZE)}。'
        )

def validate_file_extension(value):
    """验证文件扩展名"""
    ext = os.path.splitext(value.name)[1][1:].lower()
    if ext not in settings.ALLOWED_FILE_EXTENSIONS:
        raise ValidationError(
            f'不支持的文件类型。允许的类型: {", ".join(settings.ALLOWED_FILE_EXTENSIONS)}'
        )

def validate_image_extension(value):
    """验证图片扩展名"""
    ext = os.path.splitext(value.name)[1][1:].lower()
    if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f'不支持的图片类型。允许的类型: {", ".join(settings.ALLOWED_IMAGE_EXTENSIONS)}'
        )

def validate_file_content(value):
    """验证文件内容（基本检查）"""
    # 读取文件前几个字节来检查文件头
    try:
        with value.open('rb') as f:
            header = f.read(8)
            
        # 检查常见文件类型的魔数
        if header.startswith(b'\xff\xd8\xff'):  # JPEG
            return
        elif header.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
            return
        elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):  # GIF
            return
        elif header.startswith(b'RIFF') and header[8:12] == b'WEBP':  # WebP
            return
        elif header.startswith(b'%PDF'):  # PDF
            return
        elif header.startswith(b'PK'):  # ZIP
            return
        else:
            raise ValidationError('文件内容验证失败，请确保上传的是有效文件。')
    except Exception:
        raise ValidationError('无法读取文件内容，请检查文件是否损坏。')
