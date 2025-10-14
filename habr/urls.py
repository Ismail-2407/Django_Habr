from django.urls import path

from . import views


app_name = "habr"

urlpatterns = (
    [
        path("", views.ArticleListView.as_view(), name="article_list"),
        path("article/<int:pk>/", views.ArticleDetailView.as_view(), name="article_detail"),
        path("article/new/", views.ArticleCreateView.as_view(), name="article_create"),
        path("category/new/", views.CategoryCreateView.as_view(), name="category_create"),
        path("article/<int:pk>/like/", views.toggle_like, name="toggle_like"),
        path("article/<int:pk>/dislike/", views.toggle_dislike, name="toggle_dislike"),
    ]
)


