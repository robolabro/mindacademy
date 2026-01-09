from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cursuri/', views.courses_list, name='courses_list'),
    path('curs/<slug:slug>/', views.course_detail, name='course_detail'),
    path('lectie-demo/', views.demo_lesson, name='demo_lesson'),
    path('contact/', views.contact, name='contact'),
    path('locatii/', views.locations, name='locations'),
    path('termeni-si-conditii/', views.terms, name='terms'),
]