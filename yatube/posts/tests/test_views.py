from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Post, Group, Comment
from posts.forms import PostForm, CommentForm

User = get_user_model()
NUM_POST = 3
NUM_PAGE = 10


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='auth',
            first_name='J',
            last_name='K'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание 2',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(PostModelTest.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': self.post.id
                }
            ): 'posts/post_detail.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ): 'posts/profile.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={
                    'post_id': self.post.id
                }
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        first_object = response.context['page_obj'][0]
        t_author = first_object.author
        t_text = first_object.text
        t_group = first_object.group
        t_image = first_object.image
        self.assertEqual(t_author, PostModelTest.user)
        self.assertEqual(
            t_text,
            self.post.text
        )
        self.assertEqual(
            t_group,
            self.post.group
        )
        self.assertEqual(
            t_image,
            self.post.image
        )
        self.assertEqual(
            response.context.get('title'),
            'Последние обновления на сайте'
        )
        self.assertEqual(
            response.context.get('h1'),
            'Последние обновления на сайте'
        )

    def test_group_list_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            )
        )
        first_object = response.context['page_obj'][0]
        t_author = first_object.author
        t_text = first_object.text
        t_slug = first_object.group.slug
        t_group = first_object.group
        t_image = first_object.image
        self.assertEqual(
            t_text,
            self.post.text
        )
        self.assertEqual(t_author, PostModelTest.user)
        self.assertEqual(t_slug, self.group.slug)
        self.assertEqual(
            t_group,
            self.post.group
        )
        self.assertEqual(
            t_image,
            self.post.image
        )
        self.assertEqual(
            response.context.get('title'),
            'Записи группы: ' + self.group.title
        )
        self.assertEqual(
            response.context.get('h1'),
            self.group.title
        )
        self.assertEqual(
            response.context.get('description'),
            'Тестовое описание'
        )

    def test_profile_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PostModelTest.user.username}
            )
        )
        first_object = response.context['page_obj'][0]
        t_author = first_object.author
        t_text = first_object.text
        t_group = first_object.group
        t_image = first_object.image
        self.assertEqual(
            t_image,
            self.post.image
        )
        self.assertEqual(
            t_text,
            self.post.text
        )
        self.assertEqual(t_author, PostModelTest.user)
        self.assertEqual(
            t_group,
            self.post.group
        )
        self.assertEqual(
            response.context.get('author'),
            PostModelTest.user
        )
        self.assertQuerysetEqual(
            response.context.get('posts'),
            Post.objects.filter(
                author=PostModelTest.user
            ).select_related(
                'author',
                'group'
            ),
            transform=lambda x: x
        )
        self.assertEqual(
            response.context.get('title'),
            'Профайл пользователя ' + PostModelTest.user.get_full_name()
        )
        self.assertEqual(
            response.context.get('title'),
            'Профайл пользователя ' + PostModelTest.user.get_full_name()
        )
        self.assertEqual(
            response.context.get('h3'),
            Post.objects.count()
        )
        self.assertEqual(
            response.context.get('h1'),
            'Все посты пользователя ' + PostModelTest.user.get_full_name()
        )

    def test_post_detail_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': self.post.id
                }
            )
        )
        first_object = response.context['one_post']
        t_text = first_object.text
        t_author = first_object.author
        t_image = first_object.image
        self.assertEqual(
            t_image,
            self.post.image
        )
        self.assertEqual(
            t_text,
            self.post.text
        )
        self.assertEqual(t_author, PostModelTest.user)
        self.assertEqual(
            response.context.get('title'),
            self.post.text[:30]
        )

    def test_post_create_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertIsInstance(response.context.get('form'), PostForm)
        self.assertEqual(
            response.context.get('title'),
            'Новый пост'
        )
        self.assertFalse(
            response.context.get('is_edit'),
            "Условие не выполняется"
        )

    def test_post_edit_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={
                    'post_id': self.post.id
                }
            )
        )
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        first_object = response.context['post']
        t_author = first_object.author
        t_text = first_object.text
        t_image = first_object.image
        self.assertEqual(
            t_image,
            self.post.image
        )
        self.assertIsInstance(response.context.get('form'), PostForm)
        self.assertEqual(
            t_text,
            self.post.text
        )
        self.assertEqual(t_author, PostModelTest.user)
        self.assertEqual(
            response.context.get('title'),
            'Редактирование поста'
        )
        self.assertEqual(
            response.context.get('is_edit'),
            True
        )

    def test_first_page_index_contains_ten_records(self):
        cache.clear()
        Post.objects.bulk_create(
            [Post(
                author=PostModelTest.user,
                text=f'Тестовый пост {i}',
                group=self.group,
            ) for i in range(12)]
        )
        response = self.authorized_client.get(reverse('posts:index'))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context['page_obj']), NUM_PAGE)

    def test_second_page_index_contains_three_records(self):
        cache.clear()
        Post.objects.bulk_create(
            [Post(
                author=PostModelTest.user,
                text=f'Тестовый пост {i}',
                group=self.group,
            ) for i in range(12)]
        )
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertEqual(
            len(
                response.context['page_obj']
            ),
            NUM_POST
        )

    def test_first_page_group_list_contains_ten_records(self):
        Post.objects.bulk_create(
            [Post(
                author=PostModelTest.user,
                text=f'Тестовый пост {i}',
                group=self.group,
            ) for i in range(12)]
        )
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            )
        )
        self.assertEqual(len(response .context['page_obj']), NUM_PAGE)

    def test_second_page_group_list_contains_three_records(self):
        Post.objects.bulk_create(
            [Post(
                author=PostModelTest.user,
                text=f'Тестовый пост {i}',
                group=self.group,
            ) for i in range(12)]
        )
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            )
            + '?page=2'
        )
        self.assertEqual(
            len(
                response.context['page_obj']
            ),
            NUM_POST
        )

    def test_first_page_profile_contains_ten_records(self):
        Post.objects.bulk_create(
            [Post(
                author=PostModelTest.user,
                text=f'Тестовый пост {i}',
                group=self.group,
            ) for i in range(12)]
        )
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PostModelTest.user}
            )
        )
        self.assertEqual(len(response.context['page_obj']), NUM_PAGE)

    def test_first_page_profile_contains_three_records(self):
        Post.objects.bulk_create(
            [Post(
                author=PostModelTest.user,
                text=f'Тестовый пост {i}',
                group=self.group,
            ) for i in range(12)]
        )
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PostModelTest.user}
            )
            + '?page=3'
        )
        self.assertEqual(
            len(
                response.context['page_obj']
            ),
            NUM_POST
        )

    def test_group_list_page_show_correct_context_other(self):
        Post.objects.create(
            author=PostModelTest.user,
            text='Тестовый пост 0',
            group=self.group_2,
            image=self.uploaded,
        )
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug2'}
            )
        )
        first_object = response.context['page_obj'][0]
        t_text = first_object.text
        t_slug = first_object.group.slug
        t_group = first_object.group
        t_image = first_object.image
        self.assertNotEqual(
            t_text,
            self.post.text
        )
        self.assertNotEqual(t_slug, PostModelTest.group.slug)
        self.assertNotEqual(t_image, PostModelTest.post.image)

        self.assertNotEqual(
            t_group,
            self.post.group
        )

    def test_post_detail_page_can_comment_authorized(self):
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': self.post.id
                }
            )
        )
        self.assertIsInstance(response.context.get('form'), CommentForm)
        Comment.objects.create(
            author=PostModelTest.user,
            text='Тестовый пост 0',
            post=PostModelTest.post,
        )
        self.assertTrue(
            Comment.objects.filter(
                author=PostModelTest.user,
                text='Тестовый пост 0',
                post=PostModelTest.post,
            ).exists()
        )

    def test_cashe(self):
        response = self.authorized_client.get(reverse('posts:index'))
        Post.objects.all().delete()
        response1 = self.authorized_client.get(reverse('posts:index'))
        cache.clear()
        response2 = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, response1.content)
        self.assertNotEqual(response2.content, response1.content)
