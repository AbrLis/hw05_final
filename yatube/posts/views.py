from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    RedirectView,
    UpdateView,
)

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post
from .utils import DataMixin, ReverseProfileMixin, SuccessUrlDetailMixin


class PostsView(DataMixin, ListView):
    """Вывод всех постов"""

    template_name = "posts/index.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context2 = self.get_context(
            title="Последние обновления на сайте",
        )
        return {**context, **context2}

    def get_queryset(self):
        return Post.objects.select_related("group", "author").all()

class PostGroupView(DataMixin, ListView):
    """Лента постов сообщества"""

    template_name = "posts/group_list.html"
    group = None

    def dispatch(self, request, *args, **kwargs):
        self.group = get_object_or_404(Group, slug=self.kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context2 = self.get_context(
            group=self.group,
            title="Записи сообщества ",
        )
        return dict(list(context.items()) + list(context2.items()))

    def get_queryset(self):
        return (
            Post.objects.filter(group=self.group)
            .select_related("author")
            .all()
        )


class ShowPostView(DataMixin, DetailView):
    """Просмотр поста"""

    template_name = "posts/post_detail.html"
    pk_url_kwarg = "post_id"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context2 = self.get_context(
            comment_form=CommentForm(),
            comments=Comment.objects.select_related()
            .filter(post=self.object)
            .all(),
        )
        return dict(list(context.items()) + list(context2.items()))


class ShowProfileView(DataMixin, ListView):
    """Профиль пользователя"""

    model = User
    username = None
    template_name = "posts/profile.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        following = False
        if self.request.user.is_authenticated:
            following = Follow.objects.filter(
                user=self.request.user, author=self.username
            )
        context2 = self.get_context(
            username=self.username,
            title="Профайл пользователя",
            following=following,
        )
        return dict(list(context.items()) + list(context2.items()))

    def get_queryset(self):
        self.username = get_object_or_404(
            User, username=self.kwargs["username"]
        )
        return (
            self.username.posts.filter(author=self.username)
            .select_related("group")
            .all()
        )


class EditPostView(
    LoginRequiredMixin, DataMixin, SuccessUrlDetailMixin, UpdateView
):
    """Редактирование поста"""

    form_class = PostForm
    pk_url_kwarg = "post_id"
    template_name = "posts/create_post.html"

    def get_queryset(self):
        return Post.objects.filter(id=self.kwargs["post_id"])

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != self.request.user:
            return redirect("posts:post_detail", self.kwargs["post_id"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        new_post = form.save(commit=False)
        new_post.author = new_post.author
        new_post.pub_date = timezone.now()
        return super().form_valid(form)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context2 = self.get_context(is_edit=True, title="Редактирование поста")
        return dict(list(context.items()) + list(context2.items()))


class CreatePostView(LoginRequiredMixin, DataMixin, CreateView):
    """Создание поста"""

    form_class = PostForm
    template_name = "posts/create_post.html"

    def form_valid(self, form):
        new_post = form.save(commit=False)
        new_post.author = self.request.user
        return super().form_valid(form)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context2 = self.get_context(is_edit=False, title="Новый пост")
        return dict(list(context.items()) + list(context2.items()))


class AddCommentView(LoginRequiredMixin, SuccessUrlDetailMixin, FormView):
    """Добавление комментария"""

    form_class = CommentForm

    def form_valid(self, form):
        new_comment = CommentForm(
            self.request.POST or None,
            author=self.request.user,
            posts=get_object_or_404(Post, pk=self.kwargs["post_id"]),
        )
        new_comment.save()
        return super().form_valid(form)


class FollowIndexView(LoginRequiredMixin, DataMixin, ListView):
    """Список постов, на которые подписан пользователь."""

    template_name = "posts/index.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context2 = self.get_context(
            title="Лента подписок",
        )
        return {**context, **context2}

    def get_queryset(self):
        return (
            Post.objects.filter(author__following__user=self.request.user)
            .select_related("author", "group")
            .all()
        )


class ProfileFollowView(LoginRequiredMixin, ReverseProfileMixin, RedirectView):
    """Подписка на автора."""

    def get(self, request, *args, **kwargs):
        author = get_object_or_404(User, username=self.kwargs["username"])
        if request.user != author:
            Follow.objects.get_or_create(user=request.user, author=author)
        return super().get(request, *args, **kwargs)


class ProfileUnfollowView(
    LoginRequiredMixin, ReverseProfileMixin, RedirectView
):
    """Отписка от автора."""

    def get(self, request, *args, **kwargs):
        author = get_object_or_404(User, username=self.kwargs["username"])
        Follow.objects.filter(user=request.user, author=author).delete()
        return super().get(request, *args, **kwargs)
