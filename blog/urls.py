"""
URL configuration for blog app.
Defines all blog-related API endpoints using Generic Views.
"""
from django.urls import path
from .views import (
    BlogPostListCreateView,
    BlogPostDetailView,
    BlogPostViewCountView,
)

app_name = 'blog'

urlpatterns = [
    # Blog Posts
    path('', BlogPostListCreateView.as_view(), name='blogpost-list-create'),
    path('<int:pk>/', BlogPostDetailView.as_view(), name='blogpost-detail'),
    path('<int:pk>/view/', BlogPostViewCountView.as_view(), name='blogpost-view-count'),
]

