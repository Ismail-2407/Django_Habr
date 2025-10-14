from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView

from .forms import ArticleForm, CategoryForm
from .models import Article


class ArticleListView(ListView):
    model = Article
    template_name = "habr/article_list.html"
    context_object_name = "articles"


class ArticleDetailView(DetailView):
    model = Article
    template_name = "habr/article_detail.html"
    context_object_name = "article"


class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = "habr/article_form.html"
    success_url = reverse_lazy("habr:article_list")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class CategoryCreateView(LoginRequiredMixin, CreateView):
    form_class = CategoryForm
    template_name = "habr/category_form.html"
    success_url = reverse_lazy("habr:article_create")


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


