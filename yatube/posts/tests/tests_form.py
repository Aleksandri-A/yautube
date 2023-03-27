import os
import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache

from posts.forms import PostForm
from posts.models import Post, Group

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.form = PostForm()
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_create_post(self):
        cache.clear()
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост 1',
            'group': PostCreateFormTests.group.id,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': PostCreateFormTests.user.username}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост 1',
                group=PostCreateFormTests.group.id,
                author=PostCreateFormTests.user,
                image='posts/small.gif'
            ).exists()
        )
        response = (self.authorized_client.get(reverse('posts:index')))
        self.assertEqual(
            os.path.basename(response.context['posts'][0].image.name),
            form_data['image'].name
        )

    def test_edit_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост 2',
            'group': PostCreateFormTests.group_2.id,
        }
        post_id = Post.objects.latest('pub_date').id
        self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': post_id}
            ),
            data=form_data,
            follow=True
        )
        edited_post = Post.objects.get(id=post_id)
        self.assertEqual(edited_post.text, form_data['text'])
        self.assertEqual(edited_post.group.id, form_data['group'])
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост 2',
                group=PostCreateFormTests.group_2.id,
            ).exists()
        )
        self.assertEqual(Post.objects.count(), posts_count)
