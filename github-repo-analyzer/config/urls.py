"""
URL configuration for the project.

Everything user-facing lives inside the `analyzer` app. This file just
points the site root at that app's URLs and wires up the admin site.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('analyzer.urls')),
]
