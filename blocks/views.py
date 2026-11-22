from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_safe
from wagtail import hooks
from wagtail.documents import get_document_model
from wagtail.documents.models import document_served

from .blocks import starts_with_webvtt_signature

CAPTIONS_CONTENT_TYPE = "text/vtt; charset=utf-8"


@require_safe
def serve_captions(
    request: HttpRequest,
    document_id: int,
    document_filename: str,
) -> HttpResponse:
    """Serve a WebVTT caption document from the site's own origin.

    A caption ``<track>`` on a player without ``crossorigin`` is fetched in
    same-origin mode. Wagtail's document view redirects to the storage URL
    when documents live in DigitalOcean Spaces, so the browser would block
    the redirected caption file. This view streams the file instead.

    It applies the same checks as Wagtail's document view, so private
    collections stay private: the filename must match, and every
    ``before_serve_document`` hook (including collection view restrictions)
    runs first. Only ``.vtt`` documents that start with the WebVTT signature
    are served, so this cannot be used to stream other documents past the
    usual redirect, even one renamed to .vtt.
    """
    document_model = get_document_model()
    document = get_object_or_404(document_model, id=document_id)

    # Same filename check as Wagtail's view, plus captions only.
    if (
        document.filename != document_filename
        or document.file_extension.lower() != "vtt"
    ):
        raise Http404

    for hook in hooks.get_hooks("before_serve_document"):
        result = hook(document, request)
        if isinstance(result, HttpResponse):
            return result

    # Read the signature from the file that is then streamed, so remote
    # storage downloads it once.
    document.file.open("rb")
    if not starts_with_webvtt_signature(document.file):
        document.file.close()
        raise Http404
    document.file.seek(0)

    document_served.send(sender=document_model, instance=document, request=request)

    response = FileResponse(document.file, content_type=CAPTIONS_CONTENT_TYPE)
    response["Content-Length"] = document.file.size
    # Match Wagtail's document view: no inline execution, no type sniffing.
    response["Content-Security-Policy"] = "default-src 'none'"
    response["X-Content-Type-Options"] = "nosniff"
    return response
