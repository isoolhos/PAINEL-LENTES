"""WSGI config for lentes_project."""
import os

from django.core.wsgi import get_wsgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lentes_project.settings")

application = get_wsgi_application()
