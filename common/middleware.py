import re
from http import HTTPStatus

from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.urls import reverse
from django.utils.cache import patch_cache_control

from common.models import CrawlerPolicySetting


class CanonicalHostRedirectMiddleware:
    """Redirect explicitly configured hosts before Django validates the host."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        environ = request.META
        host = environ.get("HTTP_HOST", "").split(":", 1)[0].lower()
        if settings.CANONICAL_HOST and host in settings.REDIRECT_HOSTS:
            return HttpResponsePermanentRedirect(
                f"https://{settings.CANONICAL_HOST}{request.get_full_path()}",
            )
        return self.get_response(request)


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
            policy = CrawlerPolicySetting.for_request_or_default(request)
            links = [
                f'<{reverse(name)}>; rel="{rel}"; type="{content_type}"'
                for name, rel, content_type in DISCOVERY_LINKS
                if name != "llms_txt" or policy.publish_llms_txt
            ]
            response.headers.setdefault("Link", ", ".join(links))

        return response


SCRIPT_START_TAG = re.compile(rb"<script(?=[\s>/])([^>]*)>", re.IGNORECASE)

# A data-cfasync attribute and its value, quoted or not. Attribute values
# can't hold a bare quote of their own kind, so text such as
# title="data-cfasync=x" stays inside its quotes and is skipped.
CFASYNC_ATTRIBUTE = re.compile(
    rb"""("[^"]*"|'[^']*')|\sdata-cfasync(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s"'>]+))?""",
    re.IGNORECASE,
)


def _opt_script_out_of_rocket_loader(match: re.Match[bytes]) -> bytes:
    """Replace any data-cfasync value on the tag with "false"."""
    attributes = CFASYNC_ATTRIBUTE.sub(
        lambda attr: attr.group(1) or b"",
        match.group(1),
    )
    return b'<script data-cfasync="false"' + attributes + b">"


class AdminRocketLoaderOptOutMiddleware:
    """Stop Cloudflare Rocket Loader from rewriting Wagtail admin scripts.

    Rocket Loader renames every script's type to "<hash>-text/javascript"
    and runs them itself after the page loads. Wagtail keeps blank inline
    panel rows in a <template> with an inline script that sets up each
    chooser. Once renamed, that script never runs when an editor clicks
    "Add", so the new row's "Choose a page" button does nothing.
    Rocket Loader skips any script marked data-cfasync="false". See
    docs/specifications/edge_caching.md.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if (
            request.path.startswith("/admin/")
            and not response.streaming
            and not response.has_header("Content-Encoding")
            and response.get("Content-Type", "").lower().startswith("text/html")
        ):
            response.content = SCRIPT_START_TAG.sub(
                _opt_script_out_of_rocket_loader,
                response.content,
            )
            if response.has_header("Content-Length"):
                response["Content-Length"] = str(len(response.content))

        return response
