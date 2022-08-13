from django.urls import path
from . import views


app_name = 'posts'


urlpatterns = [
    # url - общие
    path(
        '',
        views.index,
        name='index'
    ),
    # url - страницы про пользователей
    path(
        'profile/<str:username>/',
        views.profile,
        name='profile'
    ),
    path(
        'follow/',
        views.follow_index,
        name='follow_index'
    ),
    path(
        'profile/<str:username>/follow',
        views.profile_follow,
        name='profile_follow'
    ),
    path(
        'profile/<str:username>/unfollow/',
        views.profile_unfollow,
        name='profile_unfollow'
    ),
    # url - страницы про группы
    path(
        'group/<slug:slug>/',
        views.group_posts,
        name='group_list'
    ),
    # url - страницы про посты
    path(
        'posts/<int:post_id>/edit/',
        views.post_edit,
        name='post_edit'
    ),
    path(
        'posts/<int:post_id>/',
        views.post_detail,
        name='post_detail'
    ),
    path(
        'create/',
        views.post_create,
        name='post_create'
    ),
    path(
        'posts/<int:post_id>/comment/',
        views.add_comment,
        name='add_comment'
    ),
]
