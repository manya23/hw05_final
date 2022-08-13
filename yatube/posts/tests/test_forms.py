import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from django.conf import settings
from ..models import Post, Group, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(
            username='Петя_authorized'
        )
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def create_test_post(self):
        """Создание записей в БД."""
        group = Group.objects.create(
            title='Котики',
            slug='cat-slug',
            description='Тут про котяток',
        )
        # создание поста, который имеет группу и автора
        post = Post.objects.create(
            pk=1,
            text='Ля-ля-ля Ля-ля-ля Ля-ля-ля Ля-ля-ля Ля-ля-ля',
            author=self.user,
            group=group,
            image=self.create_image_object('small')
        )
        return group, post

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

    def test_post_create_add_valid_data_from_form_to_db(self):
        """Тест отправления и сохранения валидной формы."""
        # подготовка
        uploaded = self.create_image_object('small')
        text_field = 'Новая запись в БД'
        post_data = [
            ('text', text_field),
            ('group', None),
            ('author', self.user),
            ('image', 'posts/small.gif'),
        ]
        success_url = reverse('posts:profile',
                              kwargs={'username': self.user.username})
        previous_post_count = Post.objects.count()
        # действие
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data={
                'text': text_field,
                'image': uploaded,
            },
            follow=True
        )
        # проверка
        self.assertEqual(Post.objects.count(), previous_post_count + 1)
        # проверка, что пост с задаными полями создан
        for (field, desired_value) in post_data:
            with self.subTest(field=desired_value):
                real_value = getattr(Post.objects.first(), field)
                self.assertEqual(real_value, desired_value)
        # после создания пользователь перенаправлен
        self.assertRedirects(response, success_url)

    def test_post_create_skip_not_valid_data_from_form(self):
        """Не валидная форма не будет отправлена и сохранена."""
        # подготовка
        posts_count = Post.objects.count()
        # действие
        self.authorized_client.post(
            reverse('posts:post_create'),
            data={
            },
            follow=True
        )
        # проверка, что пост не сохранился в БД
        self.assertEqual(Post.objects.count(), posts_count)

    def test_post_create_skip_data_from_guest_user(self):
        """Валидная форма от гостя не будет сохранена."""
        # подготовка
        text_field = 'Самая новая запись в БД'
        success_url = '/auth/login/?next=/create/'
        previous_post_count = Post.objects.count()
        # действие
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data={
                'text': text_field,
            },
            follow=True
        )
        # проверка, что количество постов не изменилось
        self.assertEqual(Post.objects.count(), previous_post_count)
        self.assertFalse(Post.objects.filter(text=text_field,
                                             group=None,
                                             author=self.user).exists())
        # гость перенаправлен на страницу входа
        self.assertRedirects(response, success_url)

    def test_post_edit_edits_existed_db_record(self):
        """Валидная форма сохраняется как обновлнение записи в БД."""
        # подготовка: заполнение БД тестовой информацией
        new_img = self.create_image_object('large')
        _, post = self.create_test_post()
        # содержание полей для отредактированного поста
        form = {
            'text': 'Пам-парам-пам-прам-пам-пам',
            'group': 1,
            'image': new_img
        }
        url = reverse('posts:post_edit',
                      kwargs={'post_id': post.pk})
        # фиксируем значения до обновления поля БД
        previous_posts_count = Post.objects.count()
        # действие: отправляем POST запрос для обновления БД
        self.authorized_client.post(url, form)
        # получаем новые данные
        updated_post = Post.objects.first()
        # проверка: поле поста обновилось, второе осталось прежним,
        # и не была добавлена новая запись
        self.assertEqual(post.group, updated_post.group)
        self.assertNotEqual(post.text, updated_post.text)
        self.assertNotEqual(post.image, updated_post.image)
        self.assertEqual(previous_posts_count, Post.objects.count())

    def test_post_edit_skip_data_from_guest(self):
        """Валидная форма не сохраняется как обновлнение записи в БД
        для гостя."""
        # подготовка: заполнение БД тестовой информацией
        group, post = self.create_test_post()
        # содержание полей для отредактированного поста
        form = {
            'text': 'Пам-парам-пам-прам-пам-пам',
            'group': 1,
        }
        url = reverse('posts:post_edit',
                      kwargs={'post_id': post.pk})
        # фиксируем значения до обновления поля БД
        previous_posts_count = Post.objects.count()
        # действие: отправляем POST запрос для обновления БД
        self.guest_client.post(url, form)
        # получаем новые данные
        new_get_response = self.authorized_client.get(url)
        form_data = new_get_response.context['form'].initial
        # проверка: пост не обновился, и не была добавлена новая запись
        self.assertEqual(post.group, group)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(previous_posts_count, Post.objects.count())

    def test_post_edit_skip_data_from_other_user(self):
        """Валидная форма не сохраняется как обновлнение записи в БД
        для авторизованного пользователя, но не автора."""
        # подготовка: заполнение БД тестовой информацией
        group, post = self.create_test_post()
        user = User.objects.create_user(
            username='Вася'
        )
        authorized_user = Client()
        authorized_user.force_login(user)
        # содержание полей для отредактированного поста
        form = {
            'text': 'Пам-парам-пам-прам-пам-пам',
            'group': 1,
        }
        url = reverse('posts:post_edit',
                      kwargs={'post_id': post.pk})
        # фиксируем значения до обновления поля БД
        previous_posts_count = Post.objects.count()
        # действие: отправляем POST запрос для обновления БД
        authorized_user.post(url, form)
        # получаем новые данные
        new_get_response = self.authorized_client.get(url)
        form_data = new_get_response.context['form'].initial
        # проверка: пост не обновился, и не была добавлена новая запись
        self.assertEqual(post.group, group)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(previous_posts_count, Post.objects.count())

    def test_add_comment_works_for_authorized(self):
        """Тест отправления и сохранения валидной формы комментария."""
        # подготовка
        post = Post.objects.create(
            pk=1,
            text='Ля-ля-ля Ля-ля-ля Ля-ля-ля',
            author=self.user,
        )
        text_field = 'Новый комментарий'
        comment_data = [
            ('text', text_field),
        ]
        success_url = reverse('posts:post_detail',
                              kwargs={'post_id': post.pk})
        previous_comment_count = Comment.objects.count()
        # действие
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': post.pk}),
            data={
                'text': text_field,
            },
            follow=True
        )
        # проверка
        self.assertEqual(Comment.objects.count(), previous_comment_count + 1)
        # проверка, что комментарий создан
        for (field, desired_value) in comment_data:
            with self.subTest(field=desired_value):
                real_value = getattr(Comment.objects.first(), field)
                self.assertEqual(real_value, desired_value)
        # после создания пользователь перенаправлен
        self.assertRedirects(response, success_url)

    def test_guest_user_not_able_to_comment(self):
        """Гость не может отправить комментарий."""
        # подготовка
        post = Post.objects.create(
            pk=1,
            text='Ля-ля-ля Ля-ля-ля Ля-ля-ля',
            author=self.user,
        )
        text_field = 'Новый комментарий'
        # действие
        self.guest_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': post.pk}),
            data={
                'text': text_field,
            },
            follow=True
        )
        # проверка
        self.assertFalse(Comment.objects.filter(text=text_field).exists())
