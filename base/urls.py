from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('habr/', include('habr.urls')),
    path('', include('habr.urls')),
]