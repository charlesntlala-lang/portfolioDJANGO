import json
from .models import SiteSettings


def site_settings(request):
    settings = SiteSettings.get_settings()
    try:
        footer_links = json.loads(settings.footer_links) if settings.footer_links else []
    except (json.JSONDecodeError, TypeError):
        footer_links = []
    try:
        social_links = json.loads(settings.social_links) if settings.social_links else {}
    except (json.JSONDecodeError, TypeError):
        social_links = {}
    return {
        'site': settings,
        'footer_links_list': footer_links,
        'social_links_dict': social_links,
    }
