from django import forms

from .models import Comment, Post
from .utils import ValidatePostFormMixin


class PostForm(forms.ModelForm, ValidatePostFormMixin):

    class Meta:
        model = Post
        fields = ("text", "group", "image")


class CommentForm(ValidatePostFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        if kwargs:
            self.user = kwargs.pop("author", None)
            self.post = kwargs.pop("posts", None)
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        comment = super().save(commit=False)
        comment.author = self.user
        comment.post = self.post
        comment.save()
        super().__init__(*args, **kwargs)
        return comment

    class Meta:
        model = Comment
        fields = ("text",)
