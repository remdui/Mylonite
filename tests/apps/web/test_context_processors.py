from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase

from apps.web.context_processors import portfolio_context


class PortfolioContextProcessorTests(SimpleTestCase):
    def test_returns_loaded_portfolio_context(self):
        request = RequestFactory().get("/")
        expected = {"portfolio_site": {"site_title": "Mylonite"}}

        with patch("apps.web.context_processors.load_portfolio_context", return_value=expected):
            context = portfolio_context(request)

        self.assertEqual(context, expected)
