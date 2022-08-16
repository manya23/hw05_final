import shutil
import tempfile

from django.core.paginator import Page
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from django.conf import settings
from ..models import User, Post, Group, Comment, Follow
from ..forms import PostForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class SingleFixtureTests(TestCase):
    """Класс для проверки функций, когда достаточно одного пользователя,
    одной группы и одного поста."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # заполнение БД тестовой информацией
        cls.group = Group.objects.create(
            title='Котики',
            slug='cat-slug',
            description='Тут про котяток',
        )
        cls.author = User.objects.create_user(username='Петя_author')
        # создание поста, который имеет группу и автора
        cls.post = Post.objects.create(
            pk=1,
            text='Ля-ля-ля Ля-ля-ля Ля-ля-ля Ля-ля-ля Ля-ля-ля',
            author=cls.author,
            group=cls.group,
            image=cls.create_image_object('small')
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.author)

        cache.clear()

    @staticmethod
    def create_image_object(img_name):
        """Создание объекта изображения."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name=f'{img_name}.gif',
            content=small_gif,
            content_type='image/gif'
        )
        return uploaded

    def test_views_for_correct_template_for_authorized(self):
        """URL-адреса используют корректные шаблоны для
        авторизованных пользователей."""
        templates_url_names = (
            (reverse('posts:follow_index'), 'posts/follow.html'),
            (reverse('posts:post_create'), 'posts/create_post.html'),
            (reverse('posts:post_edit',
                     kwargs={'post_id': SingleFixtureTests.post.pk}
                     ), 'posts/create_post.html'),
        )
        for url, template in templates_url_names:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_views_for_correct_template_for_guest(self):
        """URL-адреса используют корректные шаблоны для гостей."""
        templates_url_names = (
            (reverse('posts:index'), 'posts/index.html'),
            (reverse('posts:group_list',
                     kwargs={'slug': SingleFixtureTests.group.slug}
                     ), 'posts/group_list.html'),
            (reverse('posts:profile',
                     kwargs={'username': SingleFixtureTests.author.username}
                     ), 'posts/profile.html'),
            (reverse('posts:post_detail',
                     kwargs={'post_id': SingleFixtureTests.post.pk}
                     ), 'posts/post_detail.html'),
        )
        for url, template in templates_url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    """Проверка контекста страниц приложения"""

    def test_index_show_correct_context(self):
        """Страница '/' возвращает объекты типа Post."""
        # подготовка
        context = (
            ('author', SingleFixtureTests.post.author),
            ('group', SingleFixtureTests.post.group),
            ('text', SingleFixtureTests.post.text),
            ('pub_date', SingleFixtureTests.post.pub_date),
            ('image', SingleFixtureTests.post.image),
        )
        # действие
        response = self.guest_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        # проверка
        self.assertIsInstance(post, Post)
        cache.clear()
        check_page_context(
            self,
            'posts:index',
            'page_obj',
            context
        )

    def test_group_show_correct_context(self):
        """На страницу постов группы выводятся только посты
        группы из параметра slug. Проверка всех полей формы."""
        context = (
            ('group', SingleFixtureTests.group),
            ('author', SingleFixtureTests.post.author),
            ('text', SingleFixtureTests.post.text),
            ('pub_date', SingleFixtureTests.post.pub_date),
            ('image', SingleFixtureTests.post.image),
        )
        check_page_context(
            self,
            'posts:group_list',
            'page_obj',
            context,
            reverse_kwargs={'slug': SingleFixtureTests.group.slug}
        )

    def test_profile_show_correct_context(self):
        """На страницу постов автора выводятся только посты
        автора из параметра username. Проверка всех полей формы."""
        context = (
            ('author', SingleFixtureTests.author),
            ('group', SingleFixtureTests.post.group),
            ('text', SingleFixtureTests.post.text),
            ('pub_date', SingleFixtureTests.post.pub_date),
            ('image', SingleFixtureTests.post.image),
        )
        check_page_context(
            self,
            'posts:profile',
            'page_obj',
            context,
            reverse_kwargs={'username': SingleFixtureTests.author.username}
        )

    def test_post_detail_show_correct_context(self):
        """На странице одного поста выводятся только один пост
        с id из параметра post_id."""
        response = self.guest_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': SingleFixtureTests.post.pk})
        )
        post = response.context['post']
        context = (
            ('pk', SingleFixtureTests.post.pk),
            ('author', SingleFixtureTests.post.author),
            ('group', SingleFixtureTests.post.group),
            ('text', SingleFixtureTests.post.text),
            ('pub_date', SingleFixtureTests.post.pub_date),
            ('image', SingleFixtureTests.post.image),
        )
        self.assertIsInstance(post, Post)
        check_page_context(
            self,
            'posts:post_detail',
            'post',
            context,
            reverse_kwargs={'post_id': SingleFixtureTests.post.pk}
        )

    def test_post_edit_show_correct_context(self):
        """На странице редактирования поста выводятся форма с
        полями из form_fields, которые заполнены данными поста с
        id из параметра post_id."""
        response = self.author_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': SingleFixtureTests.post.pk})
        )
        form_fields = (
            ('text',
             (forms.fields.CharField, SingleFixtureTests.post.text)),
            ('group',
             (forms.models.ModelChoiceField, SingleFixtureTests.post.group)),
            ('image',
             (forms.ImageField, SingleFixtureTests.post.image)),
        )
        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)
        # проверка поля контекста 'form'
        for value, expected in form_fields:
            with self.subTest(value=value):
                form_field = form.fields.get(value)
                field_data = form.instance
                self.assertIsInstance(form_field, expected[0])
                self.assertEqual(getattr(field_data, value), expected[1])
        # проверка поля контекста 'is_edit'
        self.assertIn('is_edit', response.context)
        self.assertTrue(response.context.get('is_edit'))

    def test_post_create_show_correct_context(self):
        """На странице создания поста выводятся форма с
        полями из form_fields."""
        response = self.author_client.get(reverse('posts:post_create'))
        form_fields = (
            ('text', forms.fields.CharField),
            ('group', forms.models.ModelChoiceField),
            ('image', forms.ImageField),
        )
        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)
        for value, expected in form_fields:
            with self.subTest(value=value):
                form_field = form.fields.get(value)
                self.assertIsInstance(form_field, expected)

    """Проверка функционала инструмента комментирования."""

    def test_new_comment_displays_on_post_detail_page(self):
        """Созданый через форму CommentForm комментарий отображается
        на странице."""
        # действие: добавление нового комментария
        comment = Comment.objects.create(
            text='Новенький коммент',
            author=SingleFixtureTests.author,
            post=SingleFixtureTests.post,
        )
        response = self.author_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': SingleFixtureTests.post.pk})
        )
        # считываем контекст ответа страницы с нужным постом
        comments_list = response.context.get('comments')
        # проверка наличия нового комментария
        self.assertIn(comment, comments_list)

    """Проверка функционала инструмента подписок."""

    def test_self_subscription_unavailable(self):
        """Пользователь не может подписаться на самого себя."""
        # отправляем запрос для создания подписки
        self.author_client.get(reverse('posts:profile_follow',
                                       kwargs={
                                           'username': self.author.username
                                       }))
        # проверка: появилась ли подписка
        self.assertFalse(Follow.objects.filter(author=self.author,
                                               user=self.author).exists())

    def test_double_subscription_unavailable(self):
        """Пользователь не может подписаться на другого дважды."""
        # создаем нового автора
        publisher = User.objects.create_user(username='Саша_author')
        # отправляем запрос для создания подписки
        self.author_client.get(reverse('posts:profile_follow',
                                       kwargs={'username': 'Саша_author'}))
        # отправляем повторный запрос для создания подписки
        self.author_client.get(reverse('posts:profile_follow',
                                       kwargs={'username': 'Саша_author'}))
        # проверка: сколько подписок появилось
        self.assertEqual(1, Follow.objects.filter(author=publisher,
                                                  user=self.author).count())

    def test_subscribe_for_authorized_creates(self):
        """Авторизованный пользователь может подписываться на других
        авторов."""
        # создаем нового автора
        publisher = User.objects.create_user(username='Саша_author')
        # отправляем запрос для создания подписки
        self.author_client.get(reverse('posts:profile_follow',
                                       kwargs={'username': 'Саша_author'}))
        # проверка: появилась ли подписка
        self.assertTrue(Follow.objects.filter(author=publisher,
                                              user=self.author).exists())

    def test_subscribe_for_guest_doesnt_create(self):
        """Авторизованный пользователь может подписываться на других
        авторов."""
        # создаем нового автора
        publisher = User.objects.create_user(username='Саша_author')
        # отправляем запрос для создания подписки
        self.guest_client.get(reverse('posts:profile_follow',
                                      kwargs={'username': 'Саша_author'}))
        # проверка: появилась ли подписка
        self.assertFalse(Follow.objects.filter(author=publisher,
                                               user=self.author).exists())

    def test_unsubscribe_for_authorized_disappears(self):
        """Авторизованный пользователь может отписываться от других
        авторов."""
        # создаем нового автора
        publisher = User.objects.create_user(username='Саша_author')
        # создаем подписку
        Follow.objects.create(author=publisher,
                              user=self.author)
        # отправляем запрос для отмены подписки
        self.author_client.get(reverse('posts:profile_unfollow',
                                       kwargs={'username': 'Саша_author'}))
        # проверка: исчезла ли подписка
        self.assertFalse(Follow.objects.filter(author=publisher,
                                               user=self.author).exists())

    def test_new_post_displays_on_follow_index_page(self):
        """Новые посты отображаются в ленте fallow_index только у тех
        пользователей, кто подписан на автора поста."""
        # создаем автора с постом
        publisher = User.objects.create_user(username='Саша_author')
        # создание поста, который имеет группу и автора
        Post.objects.create(
            text='Ля-ля-ля Ля-ля-ля Ля-ля-ля',
            author=publisher,
            group=SingleFixtureTests.group,
        )
        # создаем пользователя, подписанного только на этого автора
        subscriber = User.objects.create_user(username='Вася_follower')
        subscriber_client = Client()
        subscriber_client.force_login(subscriber)
        # создаем подписку follower на author
        Follow.objects.create(author=publisher,
                              user=subscriber)
        # проверяем контекст страницы fallow_index для subscriber
        request = subscriber_client.get(reverse('posts:follow_index'))
        post_list = request.context['page_obj']
        for post in post_list:
            with self.subTest(post_id=post.pk):
                self.assertEqual(post.author, publisher)

        # проверяем контекст страницы fallow_index для пользователя author
        request = self.author_client.get(reverse('posts:follow_index'))
        post_list = request.context['page_obj']
        self.assertEqual(len(post_list), 0)

    """Дополнительные проверки"""

    def test_post_display_page(self):
        """Пост с указанной группой отображается на страницах: index,
        group_list - для группы, которой принадлежит пост, profile - для
        автора этого поста."""
        desired_data = (('group', SingleFixtureTests.post.group),
                        ('author', SingleFixtureTests.post.author))
        pages = (
            (reverse('posts:index'), desired_data),
            (reverse('posts:group_list',
                     kwargs={'slug': SingleFixtureTests.group.slug}
                     ), desired_data),
            (reverse('posts:profile',
                     kwargs={'username': SingleFixtureTests.author.username}
                     ), desired_data),
        )
        for (url, fields) in pages:
            for (field, desired_value) in fields:
                with self.subTest(field=field):
                    response = self.author_client.get(url)
                    post_list = response.context['page_obj']
                    field_data = [getattr(post, field) for post in post_list]
                    self.assertIn(desired_value, field_data)
                    cache.clear()

    def test_index_page_caching(self):
        """Главная страница posts:index генерируется раз в 20 секунд.
        И остальное время используется ее версия из кэша."""
        # создаем новый пост в БД
        Post.objects.create(
            text='Свежий пост',
            author=SingleFixtureTests.author,
        )
        # запоминаем кэш
        response = self.author_client.get(reverse('posts:index'))
        old_cache = response.content
        # удаляем пост
        Post.objects.filter(text='Свежий пост',
                            author=SingleFixtureTests.author).delete()
        response = self.author_client.get(reverse('posts:index'))
        new_cache = response.content
        # проверка: без очистки кэша старый и новый кэш одинаковы
        self.assertEqual(old_cache, new_cache)
        cache.clear()
        response = self.author_client.get(reverse('posts:index'))
        brand_new_cache = response.content
        # проверка: после очистки кэша старый и новый кэш отличны
        self.assertNotEqual(new_cache, brand_new_cache)


class MultiFixtureTests(TestCase):
    """Класс для проверки функций, когда нужно много пользоватей,
       группы и постов."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # заполнение БД тестовой информацией
        cls.group = Group.objects.create(
            title='Котики',
            slug='cat-slug',
            description='Тут про котяток',
        )
        cls.author = User.objects.create_user(username='Петя_author')
        cls.user_auth = User.objects.create_user(username='Коля_authorized')
        cls.user = User.objects.create_user(username='Вася')
        cls.users = [cls.author, cls.user_auth]
        # создание поста, который имеет группу и автора
        cls.post = Post.objects.create(
            pk=1,
            text='Ля-ля-ля Ля-ля-ля Ля-ля-ля Ля-ля-ля Ля-ля-ля',
            author=cls.author,
            group=MultiFixtureTests.group,
        )
        # создание дополнительных постов для тестовой БД
        cls.post_db = Post.objects.bulk_create([
            Post(
                pk=post_id,
                text=f'Пост № {post_id}: Ля-ля-ля Ля-ля-ля '
                     f'Ля-ля-ля Ля-ля-ля Ля-ля-ля',
                author=cls.get_author(post_id),
                group=cls.get_group(post_id),
            ) for post_id in range(2, 25)
        ])

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.user_client = Client()
        self.user_client.force_login(self.user_auth)

        cache.clear()

    @staticmethod
    def get_author(div_rest):
        """Выбор автора поста."""
        if div_rest % 2 == 0:
            post_author = MultiFixtureTests.users[0]
        else:
            post_author = MultiFixtureTests.users[1]

        return post_author

    @staticmethod
    def get_group(div_rest):
        """Выбор группы для поста."""
        if div_rest % 2 == 0:
            post_group = MultiFixtureTests.group
        else:
            post_group = None

        return post_group

    def test_group_show_correct_context(self):
        """На страницу постов группы выводятся только посты
        группы из параметра slug."""
        context = (
            ('group', MultiFixtureTests.group),
        )
        check_page_context(
            self,
            'posts:group_list',
            'page_obj',
            context,
            reverse_kwargs={'slug': MultiFixtureTests.group.slug}
        )

    def test_profile_show_correct_context(self):
        """На страницу постов автора выводятся только посты
        автора из параметра username."""
        context = (
            ('author', MultiFixtureTests.author),
        )
        check_page_context(
            self,
            'posts:profile',
            'page_obj',
            context,
            reverse_kwargs={'username': MultiFixtureTests.author.username}
        )

    """Тестирование паждинаторов страниц приложения"""

    def test_first_page_contains_ten_records(self):
        """На первой странице отображается максимальное число постов."""
        pages_with_pagination = (
            (reverse('posts:index'), 'page_obj'),
            (reverse('posts:group_list',
                     kwargs={'slug': MultiFixtureTests.group.slug}
                     ), 'page_obj'),
            (reverse('posts:profile',
                     kwargs={'username': MultiFixtureTests.author.username}
                     ), 'page_obj'),
        )
        for (page_path, context_key) in pages_with_pagination:
            with self.subTest(page_path=page_path):
                response = self.guest_client.get(page_path)
                self.assertEqual(
                    len(response.context[context_key]),
                    settings.PAGINATOR_PAGE_LEN
                )

    def test_second_page_contains_three_records(self):
        """На второй странице выводится различное число постов."""
        pages_with_pagination = (
            (reverse('posts:index'), ('page_obj', 10)),
            (reverse('posts:group_list',
                     kwargs={'slug': MultiFixtureTests.group.slug}
                     ), ('page_obj', 3)),
            (reverse('posts:profile',
                     kwargs={'username': MultiFixtureTests.author.username}
                     ), ('page_obj', 3)),
        )
        for (page_path, context_data) in pages_with_pagination:
            with self.subTest(page_path=page_path):
                response = self.guest_client.get(page_path + '?page=2')
                self.assertEqual(
                    len(response.context[context_data[0]]),
                    context_data[1]
                )


def check_page_context(test_class,
                       namespace,
                       context_name,
                       context_values,
                       reverse_kwargs=None):
    """Функция для проверки контекста страницы.
    :param test_class: объект класса с тестами
    :param str namespace: косвенная url
    :param str context_name: ключ в словаре контекста
    :param tuple context_values: пары (поле модели, его жалаемое значение)
    :param dict reverse_kwargs: аргументы view-функции для url"""
    # действие
    if reverse_kwargs:
        response = test_class.guest_client.get(
            reverse(namespace, kwargs=reverse_kwargs)
        )
    else:
        response = test_class.guest_client.get(reverse(namespace))
    form_list = response.context[context_name]
    if type(form_list) is not Page:
        form_list = [form_list, ]
    # проверка всех объектов на странице
    for item in form_list:
        for (field_name, desired) in context_values:
            field_value = getattr(item, field_name)
            with test_class.subTest(field=field_name):
                test_class.assertEqual(field_value, desired)
