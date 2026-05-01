"""
WSGI app wrapper for deployment platforms that expect 'app' module.
Re-exports from config.wsgi for compatibility with gunicorn app:app
"""
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from config.wsgi import application

app = application
