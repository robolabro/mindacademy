from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Course, Location, AgeGroup, Testimonial
from .forms import DemoLessonForm, ContactForm


def home(request):
    featured_courses = Course.objects.filter(is_active=True, featured=True)[:3]
    testimonials = Testimonial.objects.filter(is_approved=True)[:6]
    context = {
        'featured_courses': featured_courses,
        'testimonials': testimonials,
    }
    return render(request, 'courses/home.html', context)


def courses_list(request):
    courses = Course.objects.filter(is_active=True)
    locations = Location.objects.filter(is_active=True)
    age_groups = AgeGroup.objects.all()

    selected_location = request.GET.get('location')
    selected_age_group = request.GET.get('age_group')

    if selected_location:
        courses = courses.filter(locations__id=selected_location)

    if selected_age_group:
        courses = courses.filter(age_group__id=selected_age_group)

    context = {
        'courses': courses,
        'locations': locations,
        'age_groups': age_groups,
        'selected_location': selected_location,
        'selected_age_group': selected_age_group,
    }
    return render(request, 'courses/courses_list.html', context)


def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug, is_active=True)
    testimonials = course.testimonials.filter(is_approved=True)
    recommended_courses = Course.objects.filter(
        is_active=True,
        featured=True
    ).exclude(id=course.id)[:3]

    context = {
        'course': course,
        'testimonials': testimonials,
        'recommended_courses': recommended_courses,
    }
    return render(request, 'courses/course_detail.html', context)


def demo_lesson(request):
    if request.method == 'POST':
        form = DemoLessonForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,
                             'Mulțumim! Cererea pentru lecția demo a fost trimisă cu succes. Te vom contacta în curând!')
            return redirect('demo_lesson')
    else:
        form = DemoLessonForm()

    context = {'form': form}
    return render(request, 'courses/demo_lesson.html', context)


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Mulțumim pentru mesaj! Te vom contacta în cel mai scurt timp.')
            return redirect('contact')
    else:
        form = ContactForm()

    context = {'form': form}
    return render(request, 'courses/contact.html', context)


def locations(request):
    all_locations = Location.objects.filter(is_active=True)
    context = {'locations': all_locations}
    return render(request, 'courses/locations.html', context)


def terms(request):
    return render(request, 'courses/terms.html')