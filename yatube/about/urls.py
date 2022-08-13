from django.urls import path
from . import views

app_name = 'about'

urlpatterns = [
    # url - статичных информационных страниц
    path(
        'author/',
        views.AboutAuthorPage.as_view(),
        name='author'),
    path(
        'tech/',
        views.AboutTechPage.as_view(),
        name='tech'),
]
