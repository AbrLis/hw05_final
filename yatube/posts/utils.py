from django import forms
from django.urls import reverse_lazy

from .models import Post

POST_ON_PAGE = 10
MIN_LEN_TEXT = 10


class ValidatePostFormMixin:
    cleaned_data = None

    def clean_text(self):
        text = self.cleaned_data["text"]
        if len(text.strip()) < MIN_LEN_TEXT:
            raise forms.ValidationError("Не меньше 10 символов.")
        return text


class DataMixin:
    context_object_name = "posts"
    model = Post
    paginate_by = POST_ON_PAGE

    def get_context(self, **kwargs):
        return kwargs


class ReverseProfileMixin:
    def get_redirect_url(self, **kwargs):
        return reverse_lazy(
            "posts:profile",
            kwargs={
                "username": kwargs["username"],
            },
        )


class SuccessUrlDetailMixin:
    kwargs = None

    def get_success_url(self):
        return reverse_lazy(
            "posts:post_detail",
            kwargs={
                "post_id": self.kwargs["post_id"],
            },
        )
