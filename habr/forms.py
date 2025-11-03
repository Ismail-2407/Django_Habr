from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.utils.text import slugify

from .models import Article, Category, UserProfile, ArticleRating

User = get_user_model()


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = [
            "title",
            "category",
            "image",
            "image_url",
            "summary",
            "content",
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
            'category': forms.Select(attrs={'class': 'form-select bg-dark text-white border-secondary'}),
            'image': forms.FileInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'accept': 'image/*'}),
            'image_url': forms.URLInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
            'summary': forms.Textarea(attrs={'class': 'form-control bg-dark text-white border-secondary', 'rows': 3}),
            'content': forms.Textarea(attrs={'class': 'form-control bg-dark text-white border-secondary', 'rows': 10}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "slug"]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
            'slug': forms.TextInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
        }

    def save(self, commit: bool = True):
        instance: Category = super().save(commit=False)
        if not instance.slug:
            instance.slug = slugify(instance.name)
        if commit:
            instance.save()
        return instance


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'autofocus': True}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Create user profile
            UserProfile.objects.get_or_create(user=user, defaults={'role': 'USER'})
        return user


class RatingForm(forms.ModelForm):
    class Meta:
        model = ArticleRating
        fields = ['score']
        widgets = {
            'score': forms.NumberInput(attrs={'min': 1, 'max': 5, 'step': 1})
        }


