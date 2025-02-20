from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CommentForm, PostForm, ProfileEditForm
from .models import Category, Comment, Post, User

PAGES_NUMBER = 10


def get_posts(post_objects):
    """Отфильтрованные посты из БД"""
    return post_objects.filter(
        pub_date__lte=timezone.now(),
        is_published=True, category__is_published=True
    )


def annotate_posts_with_comments(post_objects):
    """Аннотирует посты количеством комментариев"""
    return get_posts(post_objects=post_objects).annotate(
        comment_count=Count("comments")
    )


def index(request):
    """Главная страница"""
    template = "blog/index.html"
    post_list = annotate_posts_with_comments(
        Post.objects).order_by("-pub_date")
    page_obj = get_paginator(request, post_list)
    context = {"page_obj": page_obj}
    return render(request, template, context)


def get_paginator(request, items, num=PAGES_NUMBER):
    """Создает объект пагинации"""
    paginator = Paginator(items, num)
    num_pages = request.GET.get("page")
    return paginator.get_page(num_pages)


def post_detail(request, post_id):
    """Полное описание выбранного поста"""
    template = "blog/detail.html"
    posts = get_object_or_404(Post, id=post_id)
    if request.user != posts.author:
        posts = get_object_or_404(get_posts(Post.objects), id=post_id)
    comments = posts.comments.order_by("created_at")
    form = CommentForm()
    context = {"post": posts, "form": form, "comments": comments}
    return render(request, template, context)


def category_posts(request, category_slug):
    """Посты в категории"""
    template = "blog/category.html"
    category = get_object_or_404(
        Category, slug=category_slug, is_published=True)
    post_list = annotate_posts_with_comments(
        category.posts).order_by("-pub_date")
    page_obj = get_paginator(request, post_list)
    context = {"category": category, "page_obj": page_obj}
    return render(request, template, context)


@login_required
def create_post(request):
    """Создает новый пост"""
    template = "blog/create.html"
    if request.method == "POST":
        form = PostForm(request.POST, files=request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("blog:profile", request.user)
    else:
        form = PostForm()
    context = {"form": form}
    return render(request, template, context)


def profile(request, username):
    """Возвращает профиль пользователя"""
    template = "blog/profile.html"
    user = get_object_or_404(User, username=username)
    posts_list = user.posts.annotate(comment_count=Count("comments")).order_by(
        "-pub_date"
    )
    page_obj = get_paginator(request, posts_list)
    context = {"profile": user, "page_obj": page_obj}
    return render(request, template, context)


@login_required
def edit_profile(request):
    """Редактирует профиль пользователя"""
    template = "blog/user.html"
    if request.method == "POST":
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("blog:profile", request.user)
    else:
        form = ProfileEditForm(instance=request.user)
    context = {"form": form}
    return render(request, template, context)


@login_required
def edit_post(request, post_id):
    """Редактирует пост"""
    template = "blog/create.html"
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect("blog:post_detail", post_id)

    if post.pub_date > timezone.now():
        pass

    if request.method == "POST":
        form = PostForm(request.POST, files=request.FILES, instance=post)
        if form.is_valid():
            post.save()
            return redirect("blog:post_detail", post_id)
    else:
        form = PostForm(instance=post)
    context = {"form": form}
    return render(request, template, context)


@login_required
def delete_post(request, post_id):
    """Удаляет пост блога"""
    template = "blog/create.html"
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect("blog:post_detail", post_id)
    if request.method == "POST":
        form = PostForm(request.POST or None, instance=post)
        post.delete()
        return redirect("blog:index")
    else:
        form = PostForm(instance=post)
    context = {"form": form}
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    """Добавляет комментарий к посту"""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect("blog:post_detail", post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    """Редактирует комментарий"""
    template = "blog/comment.html"
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.author:
        return redirect("blog:post_detail", post_id)
    if request.method == "POST":
        form = CommentForm(request.POST or None, instance=comment)
        if form.is_valid():
            form.save()
            return redirect("blog:post_detail", post_id)
    else:
        form = CommentForm(instance=comment)
    context = {"form": form, "comment": comment}
    return render(request, template, context)


@login_required
def delete_comment(request, post_id, comment_id):
    """Удаляет комментарий"""
    template = "blog/comment.html"
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.author:
        return redirect("blog:post_detail", post_id)
    if request.method == "POST":
        comment.delete()
        return redirect("blog:post_detail", post_id)
    context = {"comment": comment}
    return render(request, template, context)
