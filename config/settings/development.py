from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

INSTALLED_APPS.remove('whitenoise.runserver_nostatic')
MIDDLEWARE.remove('whitenoise.middleware.WhiteNoiseMiddleware')

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
