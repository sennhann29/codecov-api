import unittest
from unittest.mock import Mock, call

from django.test import RequestFactory

from codecov.middleware.utm_middleware import UTMMiddleware


class TestUTMMiddleware(unittest.TestCase):
    def test_init(self):
        middleware = UTMMiddleware("response")
        assert (middleware.get_response) == "response"

    def test_utm_middleware(self):
        mockRequest = RequestFactory().get(
            "",
            {
                "utm_department": "a",
                "utm_campaign": "b",
                "utm_medium": "c",
                "utm_source": "d",
                "utm_content": "e",
                "utm_term": "f",
            },
        )
        mockResponse = Mock()
        middleware = UTMMiddleware(mockResponse)
        middleware(mockRequest)
        set_cookies_call = mockResponse.mock_calls[1]
        assert len(mockResponse.mock_calls) == 2
        assert set_cookies_call == call().set_cookie(
            "_marketing_tags",
            "utm_department=a&utm_campaign=b&utm_medium=c&utm_source=d&utm_content=e&utm_term=f",
            max_age=86400,
            httponly=True,
            domain="localhost",
        )

    def test_utm_middleware_without_valid_params(self):
        mockRequest = RequestFactory().get(
            "", {"abc_rent": "a", "abc_sign": "b", "abc_umnn": "c",},
        )
        mockResponse = Mock()
        middleware = UTMMiddleware(mockResponse)
        middleware(mockRequest)
        assert len(mockResponse.mock_calls) == 1
