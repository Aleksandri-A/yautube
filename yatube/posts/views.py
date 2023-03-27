from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm

COUNT = 10


def group_list(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author', 'group')
    paginator = Paginator(posts, COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = 'Записи группы: ' + str(group)
    context = {
        'page_obj': page_obj,
        'group': group,
        'title': title,
        'h1': group.title,
        'description': group.description,
    }
    return render(request, 'posts/group_list.html', context)


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.select_related('author', 'group')
    paginator = Paginator(post_list, COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'posts': post_list,
        'title': 'Последние обновления на сайте',
        'h1': 'Последние обновления на сайте',
    }
    return render(request, 'posts/index.html', context)


def profile(request, username):
    # Здесь код запроса к модели и создание словаря контекста
    author = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=author).select_related(
        'author', 'group')
    paginator = Paginator(post_list, COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author
    ).exists()
    context = {
        'author': author,
        'h1': 'Все посты пользователя ' + str(author.get_full_name()),
        'title': 'Профайл пользователя ' + str(author.get_full_name()),
        'page_obj': page_obj,
        'h3': page_obj.paginator.count,
        'posts': post_list,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    one_post = get_object_or_404(Post, id=post_id)
    comments = one_post.comments.all()
    form = CommentForm(request.POST or None)
    is_author = request.user == one_post.author
    context = {
        'one_post': one_post,
        'title': one_post.text[:30],
        'is_author': is_author,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    template = 'posts/create_post.html'
    groups = Group.objects.all().order_by('title')
    context = {
        'title': 'Новый пост',
        'form': form,
        'groups': groups,
    }
    if request.method != 'POST':
        return render(request, template, context)
    if not form.is_valid():
        return render(request, template, context)
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', (request.user.username))


@login_required
def post_edit(request, post_id):
    is_edit = True
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    groups = Group.objects.all().order_by('title')
    context = {
        'title': 'Редактирование поста',
        'form': form,
        'is_edit': is_edit,
        'post': post,
        'groups': groups,
    }
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    if request.method != 'POST':
        return render(request, template, context)
    post = form.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'posts': posts,
        'title': 'Лента подписок',
        'h1': 'Лента подписок',
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    author = get_object_or_404(User, username=username)
    follower = Follow.objects.filter(user=request.user, author=author)
    if request.user != author and not follower.exists():
        Follow.objects.create(user=request.user, author=author)
    else:
        return redirect('posts:profile', (request.user.username))
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(user=request.user, author=author)
    if following.exists():
        following.delete()
    return redirect('posts:follow_index')
