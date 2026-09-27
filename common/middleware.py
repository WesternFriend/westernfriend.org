from http import HTTPStatus

from django.conf import settings
from django.urls import reverse
from django.utils.cache import patch_cache_control

# Paths that serve per-visitor content, matching the Cloudflare cache rule
PRIVATE_PATH_PREFIXES = (
    "/admin/",
    "/accounts/",
    "/cart/",
    "/orders/",
    "/payment/",
    "/paypal/",
    "/documents/",
    "/__reload__/",
)


class PublicCacheControlMiddleware:
    """Let Cloudflare cache anonymous responses that hold nothing personal.

    Cloudflare ignores Vary: Cookie and serves a cached page to everyone,
    so a response is public only when no visitor state went into it.
    Everything else is explicitly private. See
    docs/specifications/edge_caching.md.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if "Cache-Control" in response:
            return response

        if self._is_public(request, response):
            # private="Set-Cookie" lets Cloudflare cache the page without
            # storing a Set-Cookie header. Django sets no cookie on public
            # responses, but App Platform's Cloudflare layer adds a
            # __cf_bm bot-management cookie, which would otherwise stop
            # our zone caching anything.
            response["Cache-Control"] = (
                f"public, max-age={settings.PUBLIC_CACHE_BROWSER_TTL}, "
                f"s-maxage={settings.PUBLIC_CACHE_EDGE_TTL}, "
                'private="Set-Cookie"'
            )
        else:
            patch_cache_control(response, private=True)

        return response

    @staticmethod
    def _is_public(request, response):
        user = getattr(request, "user", None)
        return (
            settings.PUBLIC_CACHE_EDGE_TTL > 0
            and request.method in ("GET", "HEAD")
            and response.status_code == HTTPStatus.OK
            and not response.cookies
            and settings.SESSION_COOKIE_NAME not in request.COOKIES
            and not request.path.startswith(PRIVATE_PATH_PREFIXES)
            and not (user and user.is_authenticated)
        )


# Point agents at our machine-readable site guides (RFC 8288)
DISCOVERY_LINKS = [
    ("llms_txt", "describedby", "text/plain"),
    ("sitemap", "sitemap", "application/xml"),
]


class DiscoveryLinkHeaderMiddleware:
    """Add a Link header advertising llms.txt and the sitemap to HTML pages."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if response.get("Content-Type", "").lower().startswith("text/html"):
            links = [
                f'<{reverse(name)}>; rel="{rel}"; type="{content_type}"'
                for name, rel, content_type in DISCOVERY_LINKS
            ]
            response.headers.setdefault("Link", ", ".join(links))

        return response
