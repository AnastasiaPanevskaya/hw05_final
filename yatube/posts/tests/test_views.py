import tempfile
import shutil

from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.cache import cache

from posts.models import Post, Group, Follow


User = get_user_model()

NUMBER_OF_POST_TEST = 3
FIRST_PAGE_POST = 10
NUM_P_ALL = 13
NUMBER_GROUP = 1
NUMBER_GROUP_TEST = 0
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.authorized_user = User.objects.create_user(username='Имя')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.authorized_user)
        cls.author_user = User.objects.create_user(username='author_user')
        cls.author = Client()
        cls.author.force_login(cls.author_user)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Описание'
        )
        cls.test_group = Group.objects.create(
            title='Тестово-тестовый заголовок',
            slug='group-slug02',
            description='Тестовое описание'
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            text='Текст',
            author=cls.author_user,
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        # проверка шаблонов
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={
                        'username': self.author_user}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={
                        'post_id': self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={
                        'post_id': self.post.id}): 'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:index'))
        post = response.context.get('page_obj')
        self.assertIsNotNone(post)
        self.assertGreater(len(post), 0)
        object_01 = response.context['page_obj'][0]
        self.assertIsNotNone(object_01)
        self.assertEqual(object_01.text, self.post.text)
        self.assertEqual(object_01.group, self.post.group)
        self.assertEqual(object_01.author, self.author_user)
        self.assertEqual(object_01.image.read(), self.uploaded.open().read())

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        group = response.context.get('group')
        self.assertIsNotNone(group)
        self.assertEqual(group, self.post.group)
        post = response.context.get('page_obj')
        self.assertIsNotNone(post)
        self.assertGreater(len(post), 0)
        object_01 = response.context['page_obj'][0]
        self.assertIsNotNone(object_01)
        self.assertEqual(object_01.text, self.post.text)
        self.assertEqual(object_01.group, self.post.group)
        self.assertEqual(object_01.author, self.author_user)
        self.assertEqual(object_01.image.read(), self.uploaded.open().read())

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={
                'username': self.author_user.username}))
        author = response.context.get('author')
        self.assertIsNotNone(author)
        self.assertEqual(author, PostPagesTests.author_user)
        post = response.context.get('page_obj')
        self.assertIsNotNone(post)
        self.assertGreater(len(post), 0)
        object_01 = response.context['page_obj'][0]
        self.assertIsNotNone(object_01)
        self.assertEqual(object_01.text, self.post.text)
        self.assertEqual(object_01.group, self.post.group)
        self.assertEqual(object_01.author, self.author_user)
        self.assertEqual(object_01.image.read(), self.uploaded.open().read())

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post = response.context.get('post')
        self.assertIsNotNone(post)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.author, self.author_user)
        self.assertEqual(post.image.read(), self.uploaded.open().read())

    def test_post_create_edit_page_show_correct_context(self):
        # Шаблон post_create и post_edit, сформирован с правильным контекстом.
        address_page = (
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.ImageField
        }
        for page in address_page:
            response = self.author.get(page)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)
        response = self.author.get(reverse('posts:post_edit',
            kwargs={'post_id': self.post.id}))
        is_edit = response.context.get('is_edit')
        self.assertIsNotNone(is_edit)
        self.assertTrue(is_edit)

    def test_post_added_correctly_user2(self):
        # Пост добавляется кореектно
        group = PostPagesTests.author.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.test_group.slug}
            )
        )
        page_obj = group.context['page_obj']
        self.assertNotIn(self.post, page_obj)

    def test_cache_index(self):
        post_c = Post.objects.create(
            author=self.author_user,
            text='Проверка кэша',
            group=self.group)
        response = self.authorized_client.get(
            reverse('posts:index')).content
        post_c.delete()
        response01 = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertEqual(response, response01)
        cache.clear()
        content_before_delete = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertNotEqual(response01, content_before_delete)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.new_user = User.objects.create_user(username='new_user')
        cls.post_user = Client()
        cls.post_user.force_login(cls.new_user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for post in range(NUM_P_ALL):
            Post.objects.create(
                author=cls.new_user,
                text=f'Текст №{post}',
                group=cls.group
            )

    def test_paginator(self):
        pages = {
            reverse('posts:index'): FIRST_PAGE_POST,
            reverse('posts:index') + '?page=2': NUMBER_OF_POST_TEST,
            reverse(
                'posts:profile', kwargs={'username': self.new_user}
            ): FIRST_PAGE_POST,
            reverse(
                'posts:profile', kwargs={'username': self.new_user}
            ) + '?page=2': NUMBER_OF_POST_TEST,
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): FIRST_PAGE_POST,
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ) + '?page=2': NUMBER_OF_POST_TEST,
        }
        for page, reverse_name in pages.items():
            with self.subTest(page=page):
                response1 = PaginatorViewsTest.post_user.get(page)
                self.assertEqual(
                    len(response1.context['page_obj']), reverse_name)


class FollowerClientTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.authorized_user = User.objects.create_user(username='Имя')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.authorized_user)
        cls.author_user = User.objects.create_user(username='author_user')
        cls.author = Client()
        cls.author.force_login(cls.author_user)

    def test_autorized_subscription(self):
        # Подписка создаётся успешно
        follow_count = Follow.objects.count()
        self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={
                    'username': self.author_user}))
        follow_count01 = Follow.objects.count()
        self.assertEqual(follow_count + 1, follow_count01)
        self.assertTrue(Follow.objects.filter(
            author=self.author_user,
            user=self.authorized_user).exists())

    def test_autorized_unsubscription(self):
        Follow.objects.create(
            author=self.author_user,
            user=self.authorized_user
        )
        follow_count01 = Follow.objects.count()
        self.authorized_client.post(
            reverse('posts:profile_unfollow', kwargs={
                    'username': self.author_user}))
        unfollow_count = Follow.objects.count()
        self.assertEqual(follow_count01 - 1, unfollow_count)
        self.assertFalse(Follow.objects.filter(
            author=self.author_user,
            user=self.authorized_user).exists())

    def test_new_post_follower(self):
        new_post_follower = Post.objects.create(
            author=self.author_user,
            text='Текстовый текст'
        )
        Follow.objects.create(
            author=self.author_user,
            user=self.authorized_user
        )
        response_follower = self.authorized_client.get(
            reverse('posts:follow_index'))
        new_post = response_follower.context['page_obj']
        self.assertIn(new_post_follower, new_post)

    def test_new_post_unfollower_no_see(self):
        new_post_unfollower = Post.objects.create(
            author=self.author_user,
            text='Текстовый текст'
        )
        response_unfollower = self.authorized_client.get(
            reverse('posts:follow_index'))
        new_post = response_unfollower.context['page_obj']
        self.assertNotIn(new_post_unfollower, new_post)
