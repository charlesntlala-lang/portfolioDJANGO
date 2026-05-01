import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env')

env = os.environ.get('DJANGO_SETTINGS_MODULE_SUFFIX', 'development')

if env == 'production':
    from .production import *
else:
    from .development import *
