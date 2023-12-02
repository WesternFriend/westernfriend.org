from http import HTTPStatus
from urllib import parse

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
import sentry_sdk


class Sentry404Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Check if the response status code is 404
        if response.status_code == HTTPStatus.NOT_FOUND:
            # Get the requested route
            requested_route = request.path_info

            # Capture and send 404 error to Sentry with route information
            with sentry_sdk.push_scope() as scope:
                scope.set_tag("404_middleware", "true")
                sentry_sdk.capture_message(
                    f"Page not found: {requested_route}",
                    level="error",
                )

            # Split the requested route to form a search query
            # e.g. /page-not-found/ -> page not found
            search_query = (
                requested_route.strip("/").replace("-", " ").replace("/", " ").strip()
            )
            encoded_query = parse.quote_plus(search_query)

            # Use `reverse` to get the URL for the search view
            search_url = reverse("search") + f"?query={encoded_query}"

            # Add a message to the user
            messages.info(
                request,
                "The page you were looking for could not be found. Here are some possible matches.",
            )

            # Redirect to the search view with the search query
            return HttpResponseRedirect(search_url)

        return response
