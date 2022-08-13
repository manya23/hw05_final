from django.views.generic import CreateView
from django.urls import reverse_lazy

from .forms import CreationForm


class SignUp(CreateView):
    """Класс для формирования шаблона с формой регистрации нового
    пользователя. После успешной регистрации перенаправляет
    на главную страницу проекта."""

    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'
