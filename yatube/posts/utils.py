from .models import Post


class DataMixin:
    context_object_name = "posts"
    model = Post

    def get_context(self, **kwargs):
        return kwargs
