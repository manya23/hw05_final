from django.test import TestCase
from datetime import datetime
from ..models import User, Post, Group


class PostsModelsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test_slug',
            description='Also% test description'
        )
        cls.post = Post.objects.create(
            text='Ля-ля-ля Ля-ля-ля Ля-ля-ля Ля-ля-ля Ля-ля-ля'
                 'Ля-ля-ля Ля-ля-ля Ля-ля-ля Ля-ля-ля Ля-ля-ля',
            pub_date=datetime.today(),
            author=cls.user,
        )

    def test_post_str_method(self):
        """Проверка метода __str__ моделей приложения."""
        test_data = (
            (PostsModelsTest.post, PostsModelsTest.post.text[:15]),
            (PostsModelsTest.group, PostsModelsTest.group.title),
        )
        for (model, expected_return) in test_data:
            with self.subTest(model=model):
                self.assertEqual(str(model), expected_return)
