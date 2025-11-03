from django.urls import path

from . import views


app_name = "habr"

urlpatterns = [
    # Authentication
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    
    # Articles
    path("", views.ArticleListView.as_view(), name="article_list"),
    path("popular/", views.PopularArticleListView.as_view(), name="popular_articles"),
    path("category/<slug:slug>/", views.CategoryArticleListView.as_view(), name="category_articles"),
    path("authors/", views.AuthorListView.as_view(), name="authors"),
    path("author/<int:pk>/", views.AuthorArticleListView.as_view(), name="author_articles"),
    path("favorites/", views.FavoritesListView.as_view(), name="favorites"),
    path("article/<int:pk>/", views.ArticleDetailView.as_view(), name="article_detail"),
    path("article/new/", views.ArticleCreateView.as_view(), name="article_create"),
    path("article/<int:pk>/edit/", views.ArticleUpdateView.as_view(), name="article_update"),
    path("article/<int:pk>/delete/", views.ArticleDeleteView.as_view(), name="article_delete"),
    
    # Categories
    path("category/new/", views.CategoryCreateView.as_view(), name="category_create"),
    
    # Actions
    path("article/<int:pk>/like/", views.toggle_like, name="toggle_like"),
    path("article/<int:pk>/dislike/", views.toggle_dislike, name="toggle_dislike"),
    path("article/<int:pk>/bookmark/", views.toggle_bookmark, name="toggle_bookmark"),
    path("article/<int:pk>/rate/", views.rate_article, name="rate_article"),
    
    # Admin actions
    path("article/<int:pk>/approve/", views.approve_article, name="approve_article"),
    path("article/<int:pk>/reject/", views.reject_article, name="reject_article"),
    
    # Comments
    path("article/<int:pk>/comment/", views.add_comment, name="add_comment"),
    
    # Admin panel
    path("admin-panel/", views.admin_panel, name="admin_panel"),
    path("edit-request/<int:pk>/approve/", views.approve_edit_request, name="approve_edit_request"),
    path("edit-request/<int:pk>/reject/", views.reject_edit_request, name="reject_edit_request"),
    path("delete-request/<int:pk>/approve/", views.approve_delete_request, name="approve_delete_request"),
    path("delete-request/<int:pk>/reject/", views.reject_delete_request, name="reject_delete_request"),
    
    # Super admin
    path("manage-users/", views.manage_users, name="manage_users"),
    path("user/<int:pk>/assign-admin/", views.assign_admin_role, name="assign_admin_role"),
    path("user/<int:pk>/remove-admin/", views.remove_admin_role, name="remove_admin_role"),
    
    # Profile
    path("profile/", views.profile_view, name="profile"),
]


