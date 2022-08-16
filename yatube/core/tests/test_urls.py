from django.test import TestCase, Client
from django.contrib.auth import get_user_model
# from ...posts.models import Post

User = get_user_model()


class CustomURLTests(TestCase):

    def setUp(self) -> None:
        self.author = User.objects.create_user(username='Автор поста')
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_urls_uses_correct_template_for_guests(self):
        """URL-адрес использует соответствующий шаблон для страниц
        с оибками."""
        templates_url_names = (
            ('/non-existing_page/',
             'core/404.html'),
        )
        for (url, template) in templates_url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
