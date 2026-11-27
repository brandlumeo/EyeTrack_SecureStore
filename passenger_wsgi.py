import pymysql
pymysql.install_as_MySQLdb()

import importlib.machinery
import importlib.util

import os
import sys

# Point to public_html
PROJECT_DIR = "/home/eyetljvp/public_html/eyetrack"
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# LiteSpeed's wsgi.file_wrapper needs a real file descriptor, but WhiteNoise answers
# Range requests (how browsers load video) with a sliced file that has none, so every
# Range request crashed with "io.UnsupportedOperation: fileno" (HTTP 500). Drop the
# file wrapper for those requests only; WhiteNoise then streams the slice itself.
_django_application = application


def application(environ, start_response):
    if 'HTTP_RANGE' in environ:
        environ.pop('wsgi.file_wrapper', None)
    return _django_application(environ, start_response)
