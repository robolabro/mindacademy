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
        'site_email': 'contact@mindacademy.ro',
        'site_phone': '0740 123 456',
        'site_phone_clean': '+40740123456',
        'site_address': 'Str. Educației Nr. 15, București, Sector 1',

        # Social media
        'social_facebook': 'https://facebook.com/mindacademy',
        'social_instagram': 'https://instagram.com/mindacademy',
        'social_twitter': 'https://twitter.com/mindacademy',
        'social_linkedin': 'https://linkedin.com/company/mindacademy',

        # Cursuri populare pentru footer
        'popular_courses': popular_courses,
    }