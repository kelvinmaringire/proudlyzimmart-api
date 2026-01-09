from django.conf import settings
from django.urls import include, path
from django.contrib import admin
from rest_framework_simplejwt.views import TokenRefreshView

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

from search import views as search_views
from products import admin_views as product_admin_views

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
    
    # Products API endpoints
    path("api/products/", include("products.urls")),
    
    # Manufacturers API endpoints
    path("api/manufacturers/", include("manufacturers.urls")),
    
    # Cart API endpoints
    path("api/cart/", include("cart.urls")),
    
    # Checkout API endpoints
    path("api/checkout/", include("checkout.urls")),
    
    # JWT Token endpoints
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    # Allauth URLs (for social authentication callbacks)
    path("accounts/", include("allauth.urls")),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns = urlpatterns + [
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:
    path("", include(wagtail_urls)),
    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    path("pages/", include(wagtail_urls)),
]
