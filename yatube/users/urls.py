from django.urls import path
from django.contrib.auth.views import LogoutView, LoginView, \
    PasswordResetView, PasswordChangeView
from . import views


app_name = 'users'


urlpatterns = [
    # url - страницы для действий с авторизацией пользователя
    path(
        'logout/',
        LogoutView.as_view(template_name='users/logged_out.html'),
        name='logout'
    ),
    path(
        'login/',
        LoginView.as_view(template_name='users/login.html'),
        name='login'
    ),
    path(
        'signup/',
        views.SignUp.as_view(),
        name='signup'
    ),
    # url - страницы для операций с паролем
    path(
        'password_reset_form/',
        PasswordResetView.as_view(),
        name='password_reset_form'
    ),
    path(
        'password_change/',
        PasswordChangeView.as_view(),
        name='password_change'
    ),
]
