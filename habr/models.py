from django.conf import settings
from django.db import models
from django.db.models import Avg
from django.core.validators import MinValueValidator, MaxValueValidator


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Admin'),
        ('ADMIN', 'Admin'),
        ('USER', 'User'),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='USER')
    is_banned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    @property
    def is_super_admin(self):
        return self.role == 'SUPER_ADMIN'

    @property
    def is_admin(self):
        return self.role == 'ADMIN' or self.role == 'SUPER_ADMIN'


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Article(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="articles")
    title = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="articles")
    image = models.ImageField(upload_to='articles/', blank=True, null=True)
    image_url = models.URLField(blank=True, help_text="Alternative: use Cloudinary URL if not uploading file")
    summary = models.TextField(help_text="Short excerpt shown on the main page")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="liked_articles", blank=True)
    dislikes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="disliked_articles", blank=True)
    
    @property
    def image_display_url(self):
        """Return image URL - prefer uploaded image over URL field"""
        if self.image:
            return self.image.url
        return self.image_url if self.image_url else None

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    @property
    def likes_count(self) -> int:
        return self.likes.count()

    @property
    def dislikes_count(self) -> int:
        return self.dislikes.count()

    @property
    def rating(self) -> float:
        """Calculate article rating as arithmetic average"""
        avg_rating = self.ratings.aggregate(Avg('score'))['score__avg']
        return round(avg_rating, 2) if avg_rating else 0.0

    @property
    def is_popular(self) -> bool:
        """Check if article has rating 4+"""
        return self.rating >= 4.0


class ArticleRating(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['article', 'user']
        ordering = ['-created_at']


class Bookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmarks')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='bookmarked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'article']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} bookmarked {self.article.title}"


class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} commented on {self.article.title}"


class ArticleEditRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='edit_requests')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='edit_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Store the proposed changes
    title = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='edit_requests')
    image_url = models.URLField(blank=True)
    summary = models.TextField()
    content = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_edits')
    rejection_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Edit request for {self.article.title} by {self.user.username}"


class ArticleDeleteRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='delete_requests')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='delete_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_deletes')
    rejection_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Delete request for {self.article.title} by {self.user.username}"




