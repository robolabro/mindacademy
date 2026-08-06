"""
Semnale pentru push automat (Epic 7, Faza 4).

Când profesorul modifică EXECUȚIA în platformă (prezență sau „ce s-a lucrat"),
marcăm obiectul `sync_status='pending'`, ca un cron scurt să împingă în Airtable
doar ce s-a schimbat (nu tot, la fiecare rulare).

Important: sincronizarea (pull/push) își scrie propriile câmpuri prin
`QuerySet.update()`, care NU declanșează aceste semnale — deci marcarea „pending"
apare doar la editările reale din platformă/admin, nu la scrierile sync-ului.
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

# Câmpurile de execuție care, la modificare, cer un push.
ATT_FIELDS = ['is_present', 'absenta_anuntata', 'genereaza_recuperare',
              'notes', 'performance_rating']


def _mark_pending(sender, pk):
    sender.objects.filter(pk=pk).exclude(sync_status='pending').update(sync_status='pending')


def register():
    from teacher_platform.models import Attendance, Lesson

    @receiver(pre_save, sender=Attendance, dispatch_uid='crm_att_dirty')
    def _att_pre(sender, instance, **kw):
        # Prezență nouă → de trimis. Editare → doar dacă s-au schimbat câmpurile
        # de execuție.
        instance._push_dirty = True
        if instance.pk:
            old = sender.objects.filter(pk=instance.pk).only(*ATT_FIELDS).first()
            if old is not None:
                instance._push_dirty = any(
                    getattr(old, f) != getattr(instance, f) for f in ATT_FIELDS)

    @receiver(post_save, sender=Attendance, dispatch_uid='crm_att_mark')
    def _att_post(sender, instance, created, **kw):
        if getattr(instance, '_push_dirty', True):
            _mark_pending(sender, instance.pk)

    @receiver(pre_save, sender=Lesson, dispatch_uid='crm_lesson_dirty')
    def _lesson_pre(sender, instance, **kw):
        # Când se schimbă conținutul scris de profesor („ce s-a lucrat" sau tema).
        # Lecțiile noi (import/creare) NU se marchează aici — push-ul lor e separat.
        instance._push_dirty = False
        if instance.pk:
            old = sender.objects.filter(pk=instance.pk).only('lesson_takeaways', 'homework').first()
            if old is not None and (
                    (old.lesson_takeaways or '') != (instance.lesson_takeaways or '')
                    or (old.homework or '') != (instance.homework or '')):
                instance._push_dirty = True

    @receiver(post_save, sender=Lesson, dispatch_uid='crm_lesson_mark')
    def _lesson_post(sender, instance, created, **kw):
        if getattr(instance, '_push_dirty', False):
            _mark_pending(sender, instance.pk)
