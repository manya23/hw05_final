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
        cls.guest_urls_status = (
            ('/follow/', HTTPStatus.FOUND),
            ('/create/', HTTPStatus.FOUND),
        )
        # для авторизованых пользователей
        cls.auth_urls_status = (
            ('/follow/', HTTPStatus.OK),
            ('/create/', HTTPStatus.OK),
        )
        # список страниц и соответствующих шаблонов
        # для всех
        cls.all_urls_template = (
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
        cls.auth_urls_template = (
            ('/follow/',
             'posts/follow.html'),
            ('/create/',
             'posts/create_post.html')
        )

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

    def test_access_to_pages_for_guests(self):
        """Проверка доступности адресов проекта для гостей."""
        url_list = StaticURLTests.url_names + StaticURLTests.guest_urls_status
        for (url, desired_response) in url_list:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code,
                                 desired_response)

    def test_access_to_pages_for_auth(self):
        """Проверка доступности адресов проекта для авторизованных
        пользователей."""
        url_list = StaticURLTests.url_names + StaticURLTests.auth_urls_status
        auth_user = self.get_user_client()
        for (url, desired_response) in url_list:
            with self.subTest(url=url):
                response = auth_user.get(url)
                self.assertEqual(response.status_code,
                                 desired_response)

    def test_author_page_access(self):
        """Проверка доступа к странице редакирования поста для его автора."""
        response = self.author_client.get(f'/posts/{StaticURLTests.post.pk}'
                                          f'/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    """Тесты шаблонов"""

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон для
        отображения на странице."""
        templates_url_names = (StaticURLTests.all_urls_template
                               + StaticURLTests.auth_urls_template)
        auth_user = self.get_user_client()
        for (url, template) in templates_url_names:
            with self.subTest(url=url):
                response = auth_user.get(url)
                self.assertTemplateUsed(response, template)

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
        urls = (
            ('/follow/',
             '/auth/login/?next=/follow/'),
            ('/create/',
             '/auth/login/?next=/create/'),
            (f'/posts/{StaticURLTests.post.pk}/edit/',
             f'/auth/login/?next=/posts/{StaticURLTests.post.pk}/edit/'),
        )
        for (origin_url, redirect_url) in urls:
            with self.subTest(url=origin_url):
                response = self.guest_client.get(origin_url, follow=True)
                self.assertRedirects(response, redirect_url)

    def test_post_edit_redirect(self):
        """Проверка редиректа со страницы /posts/{self.post.pk}/edit/
        для различных случаев."""
        authorized_client = self.get_user_client()
        origin_url = f'/posts/{StaticURLTests.post.pk}/edit/'
        user_redirect = (
            (self.guest_client,
             f'/auth/login/?next={origin_url}'),
            (authorized_client,
             f'/posts/{StaticURLTests.post.pk}/'),
        )
        for (user, redirect_url) in user_redirect:
            response = user.get(origin_url, follow=True)
            with self.subTest(user=response):
                self.assertRedirects(response, redirect_url)
