import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from http import HTTPStatus

from posts.models import Post, Group, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Описание'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст записанный в форму',
            'group': self.group.id,
            'image': uploaded,
        }
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        created_post = Post.objects.last()
        self.assertEqual(Post.objects.count(),
                         posts_count + 1,
                         )
        self.assertEqual(created_post.id, form_data['group'])
        self.assertEqual(created_post.text, form_data['text'])
        self.assertEqual(created_post.author, self.user)
        self.assertEqual(created_post.image.read(), uploaded.open().read())

    def test_post_edit(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        post = Post.objects.create(text='Тестовый текст',
                                        author=self.user,
                                        group=self.group,
                                        image=uploaded
                                   )
        self.group = Group.objects.create(title='Тестовая группа',
                                          slug='test-group',
                                          description='Описание')
        form_data = {
            'text': 'Текст записанный в форму',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        edit_post = Post.objects.last()
        self.assertNotEqual(post.group, form_data['group'])
        self.assertNotEqual(post.text, form_data['text'])
        self.assertEqual(edit_post.image.read(), uploaded.open().read())

    def test_create_comment(self):
        '''комментировать посты может только авторизованный пользователь'''
        comment_count = Comment.objects.count()
        post = Post.objects.create(text='Тестовый текст',
                                        author=self.user)
        form_data = {'text': 'Тестовый коммент2'}
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': post.id}),
            data=form_data, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        comment_count01 = Comment.objects.count()
        self.assertEqual(comment_count01,
                         comment_count + 1,
                         )
        last_post = Comment.objects.last()
        self.assertEqual(last_post.text, form_data.get('text'))
