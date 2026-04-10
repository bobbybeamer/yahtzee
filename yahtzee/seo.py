from django.conf import settings
from django.urls import reverse


def absolute_url(request, path=None):
    configured_site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
    resolved_path = request.get_full_path() if path is None else path

    if configured_site_url:
        if not resolved_path.startswith('/'):
            resolved_path = f'/{resolved_path}'
        return f'{configured_site_url}{resolved_path}'

    if path is None:
        return request.build_absolute_uri()

    return request.build_absolute_uri(path)


def named_url(request, name):
    return absolute_url(request, reverse(name))