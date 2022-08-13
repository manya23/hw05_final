from http import HTTPStatus
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache

from ..models import Post, Group

User = get_user_model()


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Автор поста')
        # cls.user = User.objects.create_user(username='Не автор поста')
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

    def test_guest_access_to_pages(self):
        """Проверка доступности адресов проекта для гостей."""
        url_names = [
            ('/', HTTPStatus.OK),
            ('/follow/', HTTPStatus.FOUND),
            (f'/group/{StaticURLTests.group.slug}/', HTTPStatus.OK),
            (f'/profile/{StaticURLTests.author.username}/', HTTPStatus.OK),
            (f'/posts/{StaticURLTests.post.pk}/', HTTPStatus.OK),
            ('/non-existing_page', HTTPStatus.NOT_FOUND),
            ('/create/', HTTPStatus.FOUND),
            (f'/posts/{StaticURLTests.post.pk}/edit/', HTTPStatus.FOUND),
        ]
        for url, desired_response in url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, desired_response)

    def test_authorised_access_to_pages(self):
        """Проверка доступности адресов проекта для авторизированных
        пользователей."""
        authorized_client = self.get_user_client()
        url_names = [
            ('/', HTTPStatus.OK),
            ('/follow/', HTTPStatus.OK),
            (f'/group/{StaticURLTests.group.slug}/', HTTPStatus.OK),
            (f'/profile/{StaticURLTests.author.username}/', HTTPStatus.OK),
            (f'/posts/{StaticURLTests.post.pk}/', HTTPStatus.OK),
            ('/non-existing_page', HTTPStatus.NOT_FOUND),
            ('/create/', HTTPStatus.OK),
            (f'/posts/{StaticURLTests.post.pk}/edit/', HTTPStatus.FOUND),
        ]
        for (url, desired_response) in url_names:
            with self.subTest(url=url):
                response = authorized_client.get(url)
                self.assertEqual(response.status_code, desired_response)

    def test_author_page_access(self):
        """Проверка доступа к странице редакирования поста для его автора."""
        response = self.author_client.get(f'/posts/{StaticURLTests.post.pk}'
                                          f'/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    """Тесты шаблонов"""

    def test_urls_uses_correct_template_for_guests(self):
        """URL-адрес использует соответствующий шаблон для гостей."""
        templates_url_names = [
            ('/',
             'posts/index.html'),
            (f'/group/{StaticURLTests.group.slug}/',
             'posts/group_list.html'),
            (f'/profile/{StaticURLTests.author.username}/',
             'posts/profile.html'),
            (f'/posts/{StaticURLTests.post.pk}/',
             'posts/post_detail.html'),
        ]
        for (url, template) in templates_url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_for_authorized(self):
        """URL-адрес использует соответствующий шаблон для пользователей."""
        templates_url_names = [
            ('/',
             'posts/index.html'),
            ('/follow/',
             'posts/follow.html'),
            (f'/group/{StaticURLTests.group.slug}/',
             'posts/group_list.html'),
            (f'/profile/{StaticURLTests.author.username}/',
             'posts/profile.html'),
            (f'/posts/{StaticURLTests.post.pk}/',
             'posts/post_detail.html'),
            ('/create/',
             'posts/create_post.html'),
        ]
        for (url, template) in templates_url_names:
            with self.subTest(url=url):
                response = self.author_client.get(url)
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
