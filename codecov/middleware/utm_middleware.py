from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from utils.utm import get_utm_params


class UTMMiddleware:
    def __init__(self, get_response: HttpResponse):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request: HttpRequest):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        response = self.get_response(request)
        self._store_to_cookie_utm_tags(request, response)
        return response

    def _store_to_cookie_utm_tags(self, request, response) -> None:
        utm_params = urlencode(get_utm_params(request.GET))
        if utm_params:
            response.set_cookie(
                "_marketing_tags",
                utm_params,
                max_age=60 * 60 * 24,  # Same as state validatiy
                httponly=True,
                domain=settings.COOKIES_DOMAIN,
            )
