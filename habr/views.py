from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Avg, Count, Q

from django.utils import timezone
from .forms import ArticleForm, CategoryForm, RegisterForm, RatingForm
from .models import Article, Category, UserProfile, Bookmark, ArticleRating, Comment, ArticleEditRequest, ArticleDeleteRequest


# Authentication views
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('habr:profile')
    else:
        form = RegisterForm()
    return render(request, 'habr/register.html', {'form': form})


def login_view(request):
    from django.contrib.auth import authenticate
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Check if user is banned
            profile = getattr(user, 'profile', None)
            if profile and profile.is_banned:
                return render(request, 'habr/login.html', {'error': 'Your account has been banned.'})
            login(request, user)
            next_url = request.GET.get('next', 'habr:profile')
            if next_url.startswith('/'):
                return redirect(next_url)
            return redirect(next_url)
        else:
            return render(request, 'habr/login.html', {'error': 'Invalid username or password.'})
    return render(request, 'habr/login.html')


def logout_view(request):
    logout(request)
    return redirect('habr:article_list')


# Article views
class ArticleListView(ListView):
    model = Article
    template_name = "habr/article_list.html"
    context_object_name = "articles"

    def get_queryset(self):
        return Article.objects.filter(is_approved=True, is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class PopularArticleListView(ListView):
    model = Article
    template_name = "habr/article_list.html"
    context_object_name = "articles"

    def get_queryset(self):
        return Article.objects.filter(is_approved=True, is_published=True).annotate(
            avg_rating=Avg('ratings__score')
        ).filter(avg_rating__gte=4.0).order_by('-avg_rating', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class CategoryArticleListView(ListView):
    model = Article
    template_name = "habr/article_list.html"
    context_object_name = "articles"

    def get_queryset(self):
        category_slug = self.kwargs.get('slug')
        category = get_object_or_404(Category, slug=category_slug)
        return Article.objects.filter(category=category, is_approved=True, is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class AuthorListView(ListView):
    model = Article
    template_name = "habr/authors.html"
    context_object_name = "authors"

    def get_queryset(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.annotate(
            article_count=Count('articles', filter=Q(articles__is_approved=True, articles__is_published=True))
        ).filter(article_count__gt=0).order_by('-article_count')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class AuthorArticleListView(ListView):
    model = Article
    template_name = "habr/article_list.html"
    context_object_name = "articles"

    def get_queryset(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        author = get_object_or_404(User, pk=self.kwargs.get('pk'))
        return Article.objects.filter(author=author, is_approved=True, is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class FavoritesListView(LoginRequiredMixin, ListView):
    model = Article
    template_name = "habr/article_list.html"
    context_object_name = "articles"

    def get_queryset(self):
        user = self.request.user
        # Articles liked by the user
        liked_qs = Article.objects.filter(likes=user, is_approved=True, is_published=True)
        # Articles bookmarked by the user (through Bookmark model)
        bookmarked_qs = Article.objects.filter(bookmarked_by__user=user, is_approved=True, is_published=True)
        # Merge safely at Python level (avoid UNION/DISTINCT which can fail on SQL Server)
        combined = {a.id: a for a in list(liked_qs) + list(bookmarked_qs)}
        # Keep consistent ordering (newest first) like default Article Meta ordering
        return sorted(combined.values(), key=lambda a: a.created_at, reverse=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class ArticleDetailView(DetailView):
    model = Article
    template_name = "habr/article_detail.html"
    context_object_name = "article"

    def get_queryset(self):
        return Article.objects.filter(is_approved=True, is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['is_bookmarked'] = Bookmark.objects.filter(
                user=self.request.user,
                article=self.object
            ).exists()
            try:
                context['user_rating'] = ArticleRating.objects.get(
                    article=self.object,
                    user=self.request.user
                ).score
            except ArticleRating.DoesNotExist:
                context['user_rating'] = None
            # Check for pending edit/delete requests
            context['has_pending_edit'] = ArticleEditRequest.objects.filter(
                article=self.object,
                user=self.request.user,
                status='PENDING'
            ).exists()
            context['has_pending_delete'] = ArticleDeleteRequest.objects.filter(
                article=self.object,
                user=self.request.user,
                status='PENDING'
            ).exists()
            # Get most recent rejected requests
            rejected_edit = ArticleEditRequest.objects.filter(
                article=self.object,
                user=self.request.user,
                status='REJECTED'
            ).order_by('-created_at').first()
            context['rejected_edit'] = rejected_edit
            rejected_delete = ArticleDeleteRequest.objects.filter(
                article=self.object,
                user=self.request.user,
                status='REJECTED'
            ).order_by('-created_at').first()
            context['rejected_delete'] = rejected_delete
        context['comments'] = self.object.comments.all()
        return context


class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = "habr/article_form.html"
    success_url = reverse_lazy("habr:article_list")

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.is_approved = False  # Needs admin approval
        form.instance.is_published = False
        return super().form_valid(form)


class ArticleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = "habr/article_form.html"

    def test_func(self):
        article = self.get_object()
        user = self.request.user
        profile = getattr(user, 'profile', None)
        # Only allow users to edit their own articles (not admins directly)
        if profile and profile.is_admin:
            return True  # Admins can edit directly
        return article.author == user

    def form_valid(self, form):
        article = self.get_object()
        user = self.request.user
        profile = getattr(user, 'profile', None)
        
        # If user is admin, update directly
        if profile and profile.is_admin:
            form.instance.is_approved = False  # Needs re-approval after edit
            form.instance.is_published = False
            return super().form_valid(form)
        
        # For regular users, create an edit request
        ArticleEditRequest.objects.create(
            article=article,
            user=user,
            title=form.cleaned_data['title'],
            category=form.cleaned_data['category'],
            image_url=form.cleaned_data.get('image_url', ''),
            summary=form.cleaned_data['summary'],
            content=form.cleaned_data['content'],
            status='PENDING'
        )
        return redirect('habr:article_detail', pk=article.pk)


class ArticleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Article
    template_name = "habr/article_confirm_delete.html"

    def test_func(self):
        article = self.get_object()
        user = self.request.user
        profile = getattr(user, 'profile', None)
        # Only allow users to delete their own articles
        if profile and profile.is_admin:
            return True  # Admins can delete directly
        return article.author == user

    def delete(self, request, *args, **kwargs):
        article = self.get_object()
        user = self.request.user
        profile = getattr(user, 'profile', None)
        
        # If user is admin, delete directly
        if profile and profile.is_admin:
            return super().delete(request, *args, **kwargs)
        
        # For regular users, create a delete request
        ArticleDeleteRequest.objects.create(
            article=article,
            user=user,
            status='PENDING'
        )
        return redirect('habr:article_detail', pk=article.pk)


class CategoryCreateView(LoginRequiredMixin, CreateView):
    form_class = CategoryForm
    template_name = "habr/category_form.html"
    success_url = reverse_lazy("habr:article_create")


# Action views
@login_required
def toggle_like(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    article = get_object_or_404(Article, pk=pk)
    user = request.user
    if article.likes.filter(pk=user.pk).exists():
        article.likes.remove(user)
    else:
        article.dislikes.remove(user)
        article.likes.add(user)
    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("habr:article_detail", pk=article.pk)


@login_required
def toggle_dislike(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    article = get_object_or_404(Article, pk=pk)
    user = request.user
    if article.dislikes.filter(pk=user.pk).exists():
        article.dislikes.remove(user)
    else:
        article.likes.remove(user)
        article.dislikes.add(user)
    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("habr:article_detail", pk=article.pk)


@login_required
def toggle_bookmark(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    article = get_object_or_404(Article, pk=pk)
    user = request.user
    bookmark, created = Bookmark.objects.get_or_create(user=user, article=article)
    if not created:
        bookmark.delete()
    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("habr:article_detail", pk=article.pk)


@login_required
def rate_article(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    article = get_object_or_404(Article, pk=pk)
    user = request.user
    score = int(request.POST.get('score', 5))
    if score < 1 or score > 5:
        score = 5
    rating, created = ArticleRating.objects.update_or_create(
        article=article,
        user=user,
        defaults={'score': score}
    )
    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("habr:article_detail", pk=article.pk)


# Admin views
@login_required
def approve_article(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    article = get_object_or_404(Article, pk=pk)
    user = request.user
    profile = getattr(user, 'profile', None)
    if not profile or not profile.is_admin:
        return HttpResponseBadRequest("Only admins can approve articles")
    article.is_approved = True
    article.is_published = True
    article.save()
    return redirect('habr:article_detail', pk=article.pk)


@login_required
def reject_article(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    article = get_object_or_404(Article, pk=pk)
    user = request.user
    profile = getattr(user, 'profile', None)
    if not profile or not profile.is_admin:
        return HttpResponseBadRequest("Only admins can reject articles")
    article.is_approved = False
    article.is_published = False
    article.save()
    return redirect('habr:article_detail', pk=article.pk)


# Comment views
@login_required
def add_comment(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    article = get_object_or_404(Article, pk=pk, is_approved=True, is_published=True)
    content = request.POST.get('content', '').strip()
    if content:
        Comment.objects.create(
            article=article,
            user=request.user,
            content=content
        )
    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("habr:article_detail", pk=article.pk)


# Admin panel for managing requests
@login_required
def admin_panel(request: HttpRequest) -> HttpResponse:
    user = request.user
    profile = getattr(user, 'profile', None)
    if not profile or not profile.is_admin:
        return HttpResponseBadRequest("Only admins can access this page")
    
    edit_requests = ArticleEditRequest.objects.filter(status='PENDING').order_by('-created_at')
    delete_requests = ArticleDeleteRequest.objects.filter(status='PENDING').order_by('-created_at')
    
    context = {
        'edit_requests': edit_requests,
        'delete_requests': delete_requests,
    }
    return render(request, 'habr/admin_panel.html', context)


@login_required
def approve_edit_request(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    edit_request = get_object_or_404(ArticleEditRequest, pk=pk)
    user = request.user
    profile = getattr(user, 'profile', None)
    if not profile or not profile.is_admin:
        return HttpResponseBadRequest("Only admins can approve requests")
    
    # Apply the changes to the article
    article = edit_request.article
    article.title = edit_request.title
    article.category = edit_request.category
    article.image_url = edit_request.image_url
    article.summary = edit_request.summary
    article.content = edit_request.content
    article.is_approved = False  # Needs re-approval
    article.is_published = False
    article.save()
    
    # Update the request
    edit_request.status = 'APPROVED'
    edit_request.reviewed_at = timezone.now()
    edit_request.reviewed_by = user
    edit_request.save()
    
    return redirect('habr:admin_panel')


@login_required
def reject_edit_request(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    edit_request = get_object_or_404(ArticleEditRequest, pk=pk)
    user = request.user
    profile = getattr(user, 'profile', None)
    if not profile or not profile.is_admin:
        return HttpResponseBadRequest("Only admins can reject requests")
    
    rejection_reason = request.POST.get('rejection_reason', '').strip()
    
    edit_request.status = 'REJECTED'
    edit_request.reviewed_at = timezone.now()
    edit_request.reviewed_by = user
    edit_request.rejection_reason = rejection_reason
    edit_request.save()
    
    return redirect('habr:admin_panel')


@login_required
def approve_delete_request(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    delete_request = get_object_or_404(ArticleDeleteRequest, pk=pk)
    user = request.user
    profile = getattr(user, 'profile', None)
    if not profile or not profile.is_admin:
        return HttpResponseBadRequest("Only admins can approve requests")
    
    # Delete the article
    article = delete_request.article
    article_pk = article.pk
    article.delete()
    
    # Update the request
    delete_request.status = 'APPROVED'
    delete_request.reviewed_at = timezone.now()
    delete_request.reviewed_by = user
    delete_request.save()
    
    return redirect('habr:admin_panel')


@login_required
def reject_delete_request(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    delete_request = get_object_or_404(ArticleDeleteRequest, pk=pk)
    user = request.user
    profile = getattr(user, 'profile', None)
    if not profile or not profile.is_admin:
        return HttpResponseBadRequest("Only admins can reject requests")
    
    rejection_reason = request.POST.get('rejection_reason', '').strip()
    
    delete_request.status = 'REJECTED'
    delete_request.reviewed_at = timezone.now()
    delete_request.reviewed_by = user
    delete_request.rejection_reason = rejection_reason
    delete_request.save()
    
    return redirect('habr:admin_panel')


# Super admin views
@login_required
def manage_users(request: HttpRequest) -> HttpResponse:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = request.user
    profile = getattr(user, 'profile', None)
    if not profile or not profile.is_super_admin:
        return HttpResponseBadRequest("Only super admins can access this page")
    
    users = User.objects.all().select_related('profile')
    
    context = {'users': users}
    return render(request, 'habr/manage_users.html', context)


@login_required
def assign_admin_role(request: HttpRequest, pk: int) -> HttpResponse:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    target_user = get_object_or_404(User, pk=pk)
    user = request.user
    profile = getattr(user, 'profile', None)
    if not profile or not profile.is_super_admin:
        return HttpResponseBadRequest("Only super admins can assign roles")
    
    target_profile, created = UserProfile.objects.get_or_create(user=target_user)
    target_profile.role = 'ADMIN'
    target_profile.save()
    
    return redirect('habr:manage_users')


@login_required
def remove_admin_role(request: HttpRequest, pk: int) -> HttpResponse:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    target_user = get_object_or_404(User, pk=pk)
    user = request.user
    profile = getattr(user, 'profile', None)
    if not profile or not profile.is_super_admin:
        return HttpResponseBadRequest("Only super admins can remove roles")
    
    target_profile = getattr(target_user, 'profile', None)
    if target_profile:
        target_profile.role = 'USER'
        target_profile.save()
    
    return redirect('habr:manage_users')


# Profile views
@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    user = request.user
    profile = getattr(user, 'profile', None)
    user_articles = Article.objects.filter(author=user).order_by('-created_at')
    bookmarks = Bookmark.objects.filter(user=user).select_related('article')
    liked_articles = user.liked_articles.all()[:10]
    
    context = {
        'user': user,
        'profile': profile,
        'user_articles': user_articles,
        'bookmarks': bookmarks,
        'liked_articles': liked_articles,
    }
    return render(request, 'habr/profile.html', context)
