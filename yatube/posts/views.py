from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.shortcuts import render, get_object_or_404, redirect
from .models import User, Post, Group, Comment, Follow
from .forms import PostForm, CommentForm
from .paginator import make_pagination


@login_required
def add_comment(request, post_id):
    """Для зарегистрированных пользователей открывает страницу
    с подробной информацией о посте, где можно оставить комментарий."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


def group_posts(request, slug):
    """Возвращает заполненный шаблон страницы с информацией
    о постах группы slug."""

    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author').all()
    page_obj = make_pagination(request, post_list)

    return render(
        request,
        'posts/group_list.html',
        {'group': group, 'page_obj': page_obj}
    )


@cache_page(20, key_prefix="index_page")
def index(request):
    """Возвращает заполненный шаблон страницы со всеми
    постами из БД."""

    post_list = Post.objects.select_related('group', 'author').all()
    page_obj = make_pagination(request, post_list)

    return render(
        request,
        'posts/index.html',
        {'page_obj': page_obj}
    )


@login_required
def post_create(request):
    """При получении POST-запроса сохраняет данные в БД
    и открывает стриницу профиля автора.
        При получении GET-запроса открывает пустую форму
    для создания нового поста."""
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', post.author)

    return render(
        request,
        'posts/create_post.html',
        {'form': form}
    )


def post_detail(request, post_id):
    """Возвращает заполненный шаблон с подробной
    информацией о посте post_id."""

    post_obj = get_object_or_404(Post, pk=post_id)
    posts_comment = Comment.objects.filter(post__comments__pk=post_id)
    # posts_comment = Comment.objects.filter(post=post_obj)
    comment_form = CommentForm(request.POST or None)

    return render(
        request,
        'posts/post_detail.html',
        {
            'post': post_obj,
            'comments': posts_comment,
            'form': comment_form,
        }
    )


@login_required
def post_edit(request, post_id):
    """Для автора поста post_id:
    При получении POST-запроса обновляет данные в БД
    и открывает стриницу с подробной информацией о посте post_id.
    При получении GET-запроса открывает форму, заполненную
    данными поста post_id.
        Для других пользователей:
    Перенаправляет на страницу с подробной информацией
    о посте post_id."""
    post_obj = get_object_or_404(Post, pk=post_id)
    if request.user != post_obj.author:
        return redirect('posts:post_detail', post_id)

    post_form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post_obj
    )
    if request.method == 'POST':
        if post_form.is_valid():
            post_form.save()
            return redirect('posts:post_detail', post_id)

    return render(
        request,
        'posts/create_post.html',
        {
            'form': post_form,
            'is_edit': True,
            'post_id': post_id,
        }
    )


def profile(request, username):
    """Возвращает заполненный шаблон со всеми постами
    пользователя username - страницу профиля username."""

    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group').all()
    page_obj = make_pagination(request, post_list)

    if request.user.is_authenticated:
        following = Follow.objects.filter(author=author,
                                          user=request.user).exists()
    else:
        following = False

    return render(
        request,
        'posts/profile.html',
        {
            'page_obj': page_obj,
            'author': author,
            'following': following,
        }
    )


@login_required
def follow_index(request):
    """Страница с постами авторов, на которых подписан пользователь."""
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = make_pagination(request, post_list)

    return render(
        request,
        'posts/follow.html',
        {'page_obj': page_obj}
    )


@login_required
def profile_follow(request, username):
    """Подписка пользователя на публикации автора username."""
    author = get_object_or_404(User, username=username)

    if (
            Follow.objects.filter(author=author, user=request.user).exists()
            or request.user == author
    ):
        return redirect('posts:profile', username=username)

    Follow.objects.create(author=author,
                          user=request.user)

    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Отписка пользователя от публикаций автора username."""
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(author=author,
                             user=request.user).exists():
        Follow.objects.get(author=author,
                           user=request.user).delete()

    return redirect('posts:profile', username=username)
