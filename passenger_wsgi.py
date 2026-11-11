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
