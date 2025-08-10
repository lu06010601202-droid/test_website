from haystack import indexes
from .models import Post, Category, Tag

class PostIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    content = indexes.CharField(model_attr='content')
    author = indexes.CharField(model_attr='author__username')
    category = indexes.CharField(model_attr='category__name')
    tags = indexes.MultiValueField()
    created = indexes.DateTimeField(model_attr='created_at')
    views = indexes.IntegerField(model_attr='views')
    likes_count = indexes.IntegerField()
    comments_count = indexes.IntegerField()

    def get_model(self):
        return Post

    def index_queryset(self, using=None):
        """只索引已审核通过的帖子"""
        return self.get_model().objects.filter(status='approved')

    def prepare_tags(self, obj):
        """准备标签数据"""
        return [tag.name for tag in obj.tags.all()]

    def prepare_likes_count(self, obj):
        """准备点赞数量"""
        return obj.likes.count()

    def prepare_comments_count(self, obj):
        """准备评论数量"""
        return obj.comments.count()

class CategoryIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr='name')
    description = indexes.CharField(model_attr='description')

    def get_model(self):
        return Category

class TagIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr='name')
    description = indexes.CharField(model_attr='description')
    posts_count = indexes.IntegerField(model_attr='posts_count')

    def get_model(self):
        return Tag
