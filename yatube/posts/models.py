from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Post(models.Model):
    """Класс модели базы данных для хранения постовю"""
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Введите текст поста',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата пубикации'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        'Group',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:15]


class Group(models.Model):
    """Класс модели базы данных для хранения групп."""
    title = models.CharField(
        verbose_name='Название группы',
        max_length=200
    )
    slug = models.SlugField(
        verbose_name='Адрес группы в url',
        unique=True
    )
    description = models.TextField(
        verbose_name='Описание группы'
    )

    def __str__(self):
        return self.title


class Comment(models.Model):
    """Класс модели базы данных для хранения комментариев
    пользователей."""
    post = models.ForeignKey(
        'Post',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост',
        help_text='Комментарий оставлен этим пользователем Yatube'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Введите свое независимое мнение относительно '
                  'представленного контента',
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата пубикации'
    )

    class Meta:
        ordering = ['-created']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'Комментарий: {self.text[:15]}'


class Follow(models.Model):
    """Класс модели базы данных для хранения подписок
    пользователей друг на друга."""

    author = models.ForeignKey(
        User,
        null=True,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Публикатор'
    )
    user = models.ForeignKey(
        User,
        null=True,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='unique_follow')
        ]

    def __str__(self):
        return f'Подписка {self.user} на {self.author}'
