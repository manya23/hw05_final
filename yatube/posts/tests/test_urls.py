import copy

from http import HTTPStatus
from django.test import TestCase, Client
from django.core.cache import cache

from ..models import User, Post, Group


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Автор поста')
        cls.post = Post.objects.create(
            pk=1,
            text='Ля-ля-ля Ля-ля-ля Ля-ля-ля Ля-ля-ля Ля-ля-ля',
            author=cls.author,
        )
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание',
        )
        # список страниц и соответствующих http-статусов
        cls.url_names = (
            ('/', HTTPStatus.OK),
            (f'/group/{cls.group.slug}/', HTTPStatus.OK),
            (f'/profile/{cls.author.username}/', HTTPStatus.OK),
            (f'/posts/{cls.post.pk}/', HTTPStatus.OK),
            ('/non-existing_page', HTTPStatus.NOT_FOUND),
            (f'/posts/{cls.post.pk}/edit/', HTTPStatus.FOUND),
        )
        # для гостей
        cls.guest_urls_status = copy.deepcopy(
            cls.url_names
        ) + (('/follow/', HTTPStatus.FOUND),
             ('/create/', HTTPStatus.FOUND),)
        # для авторизованых пользователей
        cls.auth_urls_status = copy.deepcopy(
            cls.url_names
        ) + (('/follow/', HTTPStatus.OK),
             ('/create/', HTTPStatus.OK),)
        # список страниц и соответствующих шаблонов
        # для гостей
        cls.guest_urls_template = (
            ('/',
             'posts/index.html'),
            (f'/group/{cls.group.slug}/',
             'posts/group_list.html'),
            (f'/profile/{cls.author.username}/',
             'posts/profile.html'),
            (f'/posts/{cls.post.pk}/',
             'posts/post_detail.html'),
        )
        # для авторизованых пользователей
        cls.auth_urls_template = copy.deepcopy(
            cls.guest_urls_template
        ) + (('/follow/',
              'posts/follow.html'),
             ('/create/',
              'posts/create_post.html'))

    def setUp(self) -> None:
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(StaticURLTests.author)

        cache.clear()

    @staticmethod
    def get_user_client():
        user = User.objects.create_user(username='Не автор поста')
        authorized_client = Client()
        authorized_client.force_login(user)
        return authorized_client

    """Тесты доступа к страницам"""

    def test_access_to_pages(self):
        """Проверка доступности адресов проекта для пользователей."""
        client_urls_pair = (
            (self.get_user_client(), StaticURLTests.auth_urls_status),
            (self.guest_client, StaticURLTests.guest_urls_status)
        )
        for (client, url_list) in client_urls_pair:
            with self.subTest(client=client):
                for (url, desired_response) in url_list:
                    with self.subTest(url=url):
                        response = client.get(url)
                        self.assertEqual(response.status_code,
                                         desired_response)

    def test_author_page_access(self):
        """Проверка доступа к странице редакирования поста для его автора."""
        response = self.author_client.get(f'/posts/{StaticURLTests.post.pk}'
                                          f'/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    """Тесты шаблонов"""

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        client_urls_pair = (
            (self.author_client, StaticURLTests.auth_urls_template),
            (self.guest_client, StaticURLTests.guest_urls_template),
        )
        for (client, templates_url_names) in client_urls_pair:
            with self.subTest(client=client):
                for (url, template) in templates_url_names:
                    with self.subTest(url=url):
                        response = client.get(url)
                        self.assertTemplateUsed(response, template)
            cache.clear()

    def test_url_template_for_post_edit_for_author(self):
        """Проверка отображения верного шаблона на странице редакирования поста
        для его автора."""
        response = self.author_client.get(f'/posts/{StaticURLTests.post.pk}'
                                          f'/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    """Тесты редиректов"""

    def test_redirect_guest_on_auth_login(self):
        """Проверяем редиректы неавторизованного пользователя
        на страницу логина."""
        urls = [
            ('/follow/',
             '/auth/login/?next=/follow/'),
            ('/create/',
             '/auth/login/?next=/create/'),
            (f'/posts/{StaticURLTests.post.pk}/edit/',
             f'/auth/login/?next=/posts/{StaticURLTests.post.pk}/edit/'),
        ]
        for (origin_url, redirect_url) in urls:
            with self.subTest(url=origin_url):
                response = self.guest_client.get(origin_url, follow=True)
                self.assertRedirects(response, redirect_url)

    def test_post_edit_redirect(self):
        """Проверка редиректа со страницы /posts/{self.post.pk}/edit/
        для различных случаев."""
        authorized_client = self.get_user_client()
        origin_url = f'/posts/{StaticURLTests.post.pk}/edit/'
        user_redirect = [
            (self.guest_client,
             f'/auth/login/?next=/posts/{StaticURLTests.post.pk}/edit/'),
            (authorized_client,
             f'/posts/{StaticURLTests.post.pk}/'),
        ]
        for (user, redirect_url) in user_redirect:
            response = user.get(origin_url, follow=True)
            with self.subTest(user=response):
                self.assertRedirects(response, redirect_url)
