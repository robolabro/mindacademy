"""
Push nocturn (cron): execuție Mind.academy → Airtable, o dată pe zi.

Punct de intrare STABIL pentru cron-ul Railway — comportamentul se ajustează
aici, în cod, fără a schimba configurarea Railway. Trimite DOAR execuția
modificată în platformă (sync_status=pending): prezențe + „ce s-a lucrat"
(Lesson Takeaways) + temă (Homework). NU creează lecții noi în Airtable
(§4/A rămâne opt-in manual) și NU șterge duplicate (opt-in manual).

Nu scrie niciodată în „Progres Lectii" (gardă la nivel de client Airtable).

Cron Railway (start command):
    python manage.py nightly_push

Necesită AIRTABLE_TOKEN cu scope data.records:write în mediu.
Idempotent: după trimitere, execuția trimisă nu mai e „pending", deci o a
doua rulare fără schimbări noi nu trimite nimic.
"""
from django.core.management.base import BaseCommand, CommandError

from crm_sync.airtable_client import AirtableConfigError
from crm_sync.push_sync import PushSync


class Command(BaseCommand):
    help = "Push nocturn: trimite execuția modificată (prezențe + lecție) în Airtable."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help="Nu scrie nimic; doar raportează ce s-ar trimite.")

    def handle(self, *args, **opts):
        try:
            push = PushSync(
                dry_run=opts['dry_run'], grupa=None, log=self.stdout.write,
                cleanup_duplicates=False,
                only_pending=True,        # prezențe: doar ce s-a schimbat
                content_all=True,         # lecții: Completed pt. TOATE finalizate
                push_new_lessons=False,
            )
            result = push.run()
        except AirtableConfigError as exc:
            raise CommandError(str(exc))

        t = result['totals']
        style = self.style.SUCCESS if result['status'] in ('success', 'dry_run') \
            else self.style.WARNING
        self.stdout.write(style(
            f"\nPush nocturn [{result['status']}] — create: {t['created']}, "
            f"actualizate: {t['updated']}, șterse: {t['deleted']}, "
            f"sărite: {t['skipped']}, erori: {t['errors']}."))
        if result['errors']:
            for e in result['errors'][:10]:
                self.stdout.write(self.style.ERROR(f"  - {e}"))
