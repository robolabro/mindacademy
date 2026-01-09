from django import forms
from .models import DemoLesson, ContactMessage

class DemoLessonForm(forms.ModelForm):
    class Meta:
        model = DemoLesson
        fields = ['parent_name', 'parent_email', 'parent_phone', 'child_age', 'course', 'location', 'terms_accepted']
        widgets = {
            'parent_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nume complet'}),
            'parent_email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'adresa@email.com'}),
            'parent_phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '07xx xxx xxx'}),
            'child_age': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Vârsta copilului', 'min': 3, 'max': 18}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'parent_name': 'Nume părinte',
            'parent_email': 'Email părinte',
            'parent_phone': 'Telefon părinte',
            'child_age': 'Vârsta copilului',
            'course': 'Selectează cursul',
            'location': 'Selectează locația',
            'terms_accepted': 'Accept termenii și condițiile',
        }

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nume complet'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'adresa@email.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '07xx xxx xxx'}),
            'message': forms.Textarea(attrs={'class': 'form-textarea', 'placeholder': 'Scrie-ne mesajul tău...', 'rows': 5}),
        }
        labels = {
            'name': 'Nume',
            'email': 'Email',
            'phone': 'Telefon',
            'message': 'Mesaj',
        }