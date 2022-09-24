from django.urls import path
from django.views.decorators.cache import cache_page

from .views import (AddCommentView, CreatePostView, EditPostView,
                    FollowIndexView, PostGroupView, PostsView,
                    ProfileFollowView, ProfileUnfollowView, ShowPostView,
                    ShowProfileView)

app_name = "posts"


urlpatterns = [
    path(
        "",
        cache_page(20, key_prefix="index_page")(PostsView.as_view()),
        name="index",
    ),
    path("group/<slug:slug>/", PostGroupView.as_view(), name="group_list"),
    path("profile/<str:username>/", ShowProfileView.as_view(), name="profile"),
    path("posts/<int:post_id>/", ShowPostView.as_view(), name="post_detail"),
    path("create/", CreatePostView.as_view(), name="post_create"),
    path(
        "posts/<int:post_id>/edit/", EditPostView.as_view(), name="post_edit"
    ),
    path(
        "posts/<int:post_id>/comment/",
        AddCommentView.as_view(),
        name="add_comment",
    ),
    path("follow/", FollowIndexView.as_view(), name="follow_index"),
    path(
        "profile/<str:username>/follow/",
        ProfileFollowView.as_view(),
        name="profile_follow",
    ),
    path(
        "profile/<str:username>/unfollow/",
        ProfileUnfollowView.as_view(),
        name="profile_unfollow",
    ),
]
