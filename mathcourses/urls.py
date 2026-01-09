"""mathcourses URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Cursuri publice (homepage, cursuri, contact, etc.)
    path('', include('courses.urls')),

    # Autentificare (login, logout, etc.)
    # path('accounts/', include('accounts.urls')),  # ← Vom crea mai târziu

    # Platforma profesori
    # path('teacher/', include('teacher_platform.urls')),  # ← Vom crea mai târziu

    # Platforma elevi
    # path('student/', include('student_platform.urls')),  # ← Vom crea mai târziu

    # Simulator Soroban
    # path('soroban/', include('soroban.urls')),
]

# Servește fișierele media și static în development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)