from .seo import absolute_url, named_url


def seo_context(request):
    return {
        'current_absolute_url': absolute_url(request),
        'site_name': 'Game Hub',
        'default_social_image_url': named_url(request, 'social_preview'),
        'default_social_image_alt': 'Game Hub preview for Yahtzee and The Maths Square',
        'default_favicon_url': named_url(request, 'favicon_svg'),
    }