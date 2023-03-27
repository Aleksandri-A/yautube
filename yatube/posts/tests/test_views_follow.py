from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Post, Follow

User = get_user_model()


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='Author',
            first_name='J',
            last_name='K'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_client2 = Client()
        self.user_who_not_follows_author = User.objects.create_user(
            username='Not Follower')
        self.authorized_client2.force_login(self.user_who_not_follows_author)
        self.authorized_client = Client()
        self.user_who_follows_author = User.objects.create_user(
            username='Follower')
        self.authorized_client.force_login(self.user_who_follows_author)

    def test_authorized_client_delete_author(self):
        cache.clear()
        self.authorized_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user}))
        self.authorized_client.post(
            reverse('posts:profile_unfollow', kwargs={'username': self.user}))
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_who_follows_author,
                author=self.user
            ).exists()
        )

    def test_authorized_client_follow_author(self):
        self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user}
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_who_follows_author,
                author=self.user
            ).exists()
        )

    def test_authorized_client_follow_author_post(self):
        cache.clear()
        response_before_following = self.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertNotIn(
            self.post, response_before_following.context.get('posts'))

        response_before_following2 = self.authorized_client2.get(
            reverse('posts:follow_index'))
        self.assertNotIn(
            self.post, response_before_following2.context.get('posts'))

        self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={'username': self.user}))
        response_after_following = self.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertIn(self.post, response_after_following.context.get('posts'))

        response_after_following2 = self.authorized_client2.get(
            reverse('posts:follow_index'))
        self.assertNotIn(
            self.post, response_after_following2.context.get('posts'))
