from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

from .models import Category, Article, UserProfile, Bookmark, ArticleRating, Comment, ArticleEditRequest, ArticleDeleteRequest

User = get_user_model()


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "is_banned")
    list_filter = ("role", "is_banned")
    search_fields = ("user__username", "user__email")
    actions = ['make_admin', 'make_super_admin', 'unban_users']

    def make_admin(self, request, queryset):
        queryset.update(role='ADMIN')
        self.message_user(request, 'Selected users are now admins.')
    make_admin.short_description = "Make selected users admins"

    def make_super_admin(self, request, queryset):
        queryset.update(role='SUPER_ADMIN')
        self.message_user(request, 'Selected users are now super admins.')
    make_super_admin.short_description = "Make selected users super admins"

    def unban_users(self, request, queryset):
        queryset.update(is_banned=False)
        self.message_user(request, 'Selected users have been unbanned.')
    unban_users.short_description = "Unban selected users"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "is_approved", "is_published", "created_at")
    list_filter = ("category", "is_approved", "is_published", "created_at")
    search_fields = ("title", "summary", "content", "author__username")
    actions = ['approve_articles', 'reject_articles']

    def approve_articles(self, request, queryset):
        queryset.update(is_approved=True, is_published=True)
        self.message_user(request, 'Selected articles have been approved.')
    approve_articles.short_description = "Approve selected articles"

    def reject_articles(self, request, queryset):
        queryset.update(is_approved=False, is_published=False)
        self.message_user(request, 'Selected articles have been rejected.')
    reject_articles.short_description = "Reject selected articles"


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("user", "article", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "article__title")


@admin.register(ArticleRating)
class ArticleRatingAdmin(admin.ModelAdmin):
    list_display = ("article", "user", "score", "created_at")
    list_filter = ("score", "created_at")
    search_fields = ("article__title", "user__username")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("article", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("article__title", "user__username", "content")


@admin.register(ArticleEditRequest)
class ArticleEditRequestAdmin(admin.ModelAdmin):
    list_display = ("article", "user", "status", "created_at", "reviewed_by", "reviewed_at")
    list_filter = ("status", "created_at")
    search_fields = ("article__title", "user__username")
    readonly_fields = ("created_at", "reviewed_at")


@admin.register(ArticleDeleteRequest)
class ArticleDeleteRequestAdmin(admin.ModelAdmin):
    list_display = ("article", "user", "status", "created_at", "reviewed_by", "reviewed_at")
    list_filter = ("status", "created_at")
    search_fields = ("article__title", "user__username")
    readonly_fields = ("created_at", "reviewed_at")



