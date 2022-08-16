from django.contrib import admin
from .models import Post, Group, Comment, Follow


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Создание объекта для настройки параметров админки."""
    list_display = ('pk', 'text', 'pub_date', 'author', 'group')
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """Создание объекта для настройки параметров админки."""
    list_display = ('title', 'slug')
    search_fields = ('description',)
    list_filter = ('title',)
    empty_value_display = '-пусто-'
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Создание объекта для настройки параметров админки."""
    list_display = ('post', 'author', 'text', 'created')
    search_fields = ('description',)
    list_filter = ('created',)
    empty_value_display = '-пусто-'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Создание объекта для настройки параметров админки."""
    list_display = ('author', 'user')
    search_fields = ('description',)
    empty_value_display = '-пусто-'
