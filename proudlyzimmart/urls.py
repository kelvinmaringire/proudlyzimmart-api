import os

from django.conf import settings
from django.urls import include, path
from django.contrib import admin
from django.views.static import serve
from rest_framework_simplejwt.views import TokenRefreshView

from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

from search import views as search_views
from products import admin_views as product_admin_views
from home.views import serve_spa

urlpatterns = [
    path("django-admin/", admin.site.urls),
    # Product import/export URLs (must be before wagtailadmin_urls)
    path("admin/products/product/import/", product_admin_views.product_import_view, name="product_import"),
    path("admin/products/product/export/", product_admin_views.product_export_view, name="product_export"),
    path("admin/products/category/import/", product_admin_views.category_import_view, name="category_import"),
    path("admin/products/category/export/", product_admin_views.category_export_view, name="category_export"),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("search/", search_views.search, name="search"),
    
    # Accounts API endpoints
    path("api/accounts/", include("accounts.urls")),
    
    # Core API endpoints
    path("api/core/", include("core.urls")),
    
    # Products API endpoints
    path("api/products/", include("products.urls")),
    
    # Manufacturers API endpoints
    path("api/manufacturers/", include("manufacturers.urls")),
    
    # Blog API endpoints
    path("api/blog/", include("blog.urls")),
    
    # Cart API endpoints
    path("api/cart/", include("cart.urls")),
    
    # Checkout API endpoints
    path("api/checkout/", include("checkout.urls")),
    
    # JWT Token endpoints
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    # Allauth URLs (for social authentication callbacks)
    path("accounts/", include("allauth.urls")),
    # Serve static assets from www/ at /assets/, /icons/, favicons
    path("assets/<path:path>", serve, {"document_root": os.path.join(settings.BASE_DIR, "www", "assets")}),
    path("icons/<path:path>", serve, {"document_root": os.path.join(settings.BASE_DIR, "www", "icons")}),
    path("favicon.ico", serve, {"document_root": settings.BASE_DIR, "path": "www/favicon.ico"}),
    path("favicon.png", serve, {"document_root": settings.BASE_DIR, "path": "www/favicon.png"}),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# SPA catch-all: serve index.html for all other routes (must be last)
urlpatterns += [
    path("", serve_spa, name="spa"),
    path("<path:path>", serve_spa),
]
