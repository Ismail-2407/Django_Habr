from django import forms
from django.utils.text import slugify

from .models import Article, Category


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = [
            "title",
            "category",
            "image_url",
            "summary",
            "content",
        ]


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "slug"]

    def save(self, commit: bool = True):
        instance: Category = super().save(commit=False)
        if not instance.slug:
            instance.slug = slugify(instance.name)
        if commit:
            instance.save()
        return instance


