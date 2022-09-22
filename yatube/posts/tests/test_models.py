from django.contrib.auth import get_user_model
from django.test import TestCase
from posts.models import Post, Group

User = get_user_model()

LEN_OF_POSTS = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа у которой много букв',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост, тут больше символов',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        self.assertEqual(str(group), group.title)

        post = PostModelTest.post
        self.assertEqual(str(post), post.text[:LEN_OF_POSTS])
