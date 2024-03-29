from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static


handler404 = 'core.views.page_not_found'
handler403 = 'core.views.csrf_failure'
handler500 = 'core.views.internal_server_error'


urlpatterns = [
    # url - общие
    path(
        '',
        include('posts.urls', namespace='posts')
    ),
    path(
        'about/',
        include('about.urls', namespace='about')
    ),
    # url - страницы про пользователей
    path(
        'admin/',
        admin.site.urls
    ),
    path(
        'auth/',
        include('users.urls')
    ),
    path(
        'auth/',
        include('django.contrib.auth.urls')
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
