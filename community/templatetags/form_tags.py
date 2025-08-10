from django import template

register = template.Library()

@register.filter(name='addclass')
def addclass(field, css):
    """为表单字段添加CSS类"""
    return field.as_widget(attrs={"class": css}) 