from http import HTTPStatus
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

        return response
