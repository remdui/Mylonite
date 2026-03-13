from django.test import SimpleTestCase

from mylonite.wsgi import application


class WsgiTests(SimpleTestCase):
    def test_wsgi_application_is_callable(self):
        self.assertTrue(callable(application))
