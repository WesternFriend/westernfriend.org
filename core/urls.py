from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.contrib.sitemaps.views import sitemap
from wagtail.documents import urls as wagtaildocs_urls

from accounts.views import (
    CustomRegistrationView,
    CustomPasswordResetView,
    CustomLoginView,
)
from search import views as search_views

handler404 = "common.views.custom_404"

urlpatterns = [
    path(
        "accounts/register/",
        CustomRegistrationView.as_view(),
        name="django_registration_register",
    ),
    path(
        "accounts/login/",
        CustomLoginView.as_view(),
        name="login",
    ),
    path(
        "accounts/password_reset/",
        CustomPasswordResetView.as_view(),
        name="password_reset",
    ),
    path("accounts/", include("django_registration.backends.activation.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("admin/", include(wagtailadmin_urls)),
    path("cart/", include("cart.urls", namespace="cart")),
    path("orders/", include("orders.urls", namespace="orders")),
    path("payment/", include("payment.urls", namespace="payment")),
    path("paypal/", include("paypal.urls", namespace="paypal")),
    path("documents/", include(wagtaildocs_urls)),
    path("search/", search_views.search, name="search"),
    path("tags/", include("tags.urls", namespace="tags")),
    path("sitemap.xml", sitemap),
    path("__reload__/", include("django_browser_reload.urls")),
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:
    path("", include(wagtail_urls)),
]


if settings.DEBUG:
    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
