from django import forms
from django.shortcuts import get_object_or_404

from users.forms import User
from .models import Post, Comment

MIN_LEN_TEXT = 10


class PostForm(forms.ModelForm):
    def clean_text(self):
        text = self.cleaned_data["text"]
        if text.strip() == "" or len(text) < MIN_LEN_TEXT:
            raise forms.ValidationError("Не меньше 10 символов.")
        return text

    class Meta:
        model = Post
        fields = ("text", "group", "image")


class CommentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        if kwargs:
            self.user = kwargs.pop('author', None)
            self.post = kwargs.pop('posts', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        comment = super().save(commit=False)
        comment.author = self.user
        comment.post = self.post
        if commit:
            comment.save()
        return comment

    def clean_text(self):
        text = self.cleaned_data["text"]
        if text.strip() == "" or len(text) < MIN_LEN_TEXT:
            raise forms.ValidationError("Не меньше 10 символов.")
        return text

    class Meta:
        model = Comment
        fields = ("text",)
