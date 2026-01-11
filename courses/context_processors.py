from .models import Course


def global_settings(request):
    """
    Context processor care adaugă setări globale în toate template-urile
    """
    # Cursuri populare pentru footer
    popular_courses = Course.objects.filter(
        is_active=True,
        featured=True
    ).order_by('-featured', 'title')[:5]

    return {
        # Informații contact
        'site_name': 'MindAcademy',
        'site_email': 'train@mindacademy.ro',
        'site_phone': '0751 746 746',
        'site_phone_clean': '+40751746746',
        'site_address': 'Str. Mitropolit Varlaam nr. 127, Sector 1, București',

        # Social media
        'social_facebook': 'https://facebook.com/mindacademy',
        'social_instagram': 'https://instagram.com/mindacademy',
        'social_twitter': 'https://twitter.com/mindacademy',
        'social_linkedin': 'https://linkedin.com/company/mindacademy',

        # Cursuri populare pentru footer
        'popular_courses': popular_courses,
    }