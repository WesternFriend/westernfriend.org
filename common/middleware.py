from django.urls import reverse

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
