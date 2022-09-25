from urllib import response
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Post, Group, User
from http import HTTPStatus

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.authorized_client = Client()
        cls.authorized_user = User.objects.create_user(username='Имя')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Описание'
        )
        cls.post = Post.objects.create(
            text='Текст',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.author_post = Client()
        self.author_post.force_login(self.user)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.authorized_user)

    def test_cheking_templates(self):
        # Правилные шаблоны
        all_templates = {
            '/': 'posts/index.html',
            f'/group/{PostURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostURLTests.user.username}/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.id}/': 'posts/post_detail.html'
        }
        for address, template in all_templates.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

        authorized_templates = {
            '/create/': 'posts/post_create.html'
        }
        # Авторизованный клиент
        for address, template in authorized_templates.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

        edit_templates = {
            f'/posts/{PostURLTests.post.id}/edit/': 'posts/post_create.html'
        }
        for address, template in edit_templates.items():
            with self.subTest(address=address):
                response = self.author_post.get(address)
                self.assertTemplateUsed(response, template)

    def test_pages_all(self):
        # Доступ автр. пользователя
        pages = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK,
            f'/posts/{self.post.id}/edit/': HTTPStatus.FOUND
        }
        for address, value in pages.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, value)

    def test_create_url_redirect_anonim(self):
        """ Проверяет редирект неавторизованного клиента ,
        старница создания поста и ред.поста"""
        login_url = reverse('users:login')
        page_noaut = {
            ('/create/'): (f'{login_url}?next=/create/'),
            (f'/posts/{self.post.id}/edit/'):
                ( f'{login_url}?next=/posts/{self.post.id}/edit/'),
            (f'/posts/{self.post.id}/comment/'):
                (f'{login_url}?next=/posts/{self.post.id}/comment/'),
            (f'/profile/{self.user}/follow/'):
                (f'{login_url}?next=/profile/{self.user}/follow/'),
            (f'/profile/{self.user}/unfollow/'):
                (f'{login_url}?next=/profile/{self.user}/unfollow/')
        }
        for page, page_address in page_noaut.items():
            with self.subTest(page_address=page_address):
                response = self.guest_client.get(page, follow=True)
                self.assertRedirects(response, page_address)

    def test_post_edit_redirect(self):
        """ Проверяет редирект авторизованного клиента ,
        старница редакт. поста"""
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/',
                                              follow=True)
        self.assertRedirects(
            response, (f'/posts/{self.post.id}/'))


class ViewTestClass(TestCase):
    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND, 404)
        self.assertTemplateUsed(response, "core/404.html")
