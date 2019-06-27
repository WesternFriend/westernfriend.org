from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.urls import path
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.contrib.sitemaps.views import sitemap
from wagtail.core import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtailautocomplete.urls.admin import urlpatterns as autocomplete_admin_urls

from magazine import urls as magazine_urls
from search import views as search_views

urlpatterns = [
    url(r"^django-admin/", admin.site.urls),
    path("accounts/", include("django_registration.backends.one_step.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    url(r"^admin/autocomplete/", include(autocomplete_admin_urls)),
    url(r"^admin/", include(wagtailadmin_urls)),
    path('cart/', include('cart.urls', namespace='cart')),
    path("magazine/", include(magazine_urls), name="magazine"),
    url(r"^documents/", include(wagtaildocs_urls)),
    url(r"^search/$", search_views.search, name="search"),
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:
    url("^sitemap\.xml$", sitemap),
    url(r"", include(wagtail_urls)),
    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    url(r'^pages/', include(wagtail_urls)),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
