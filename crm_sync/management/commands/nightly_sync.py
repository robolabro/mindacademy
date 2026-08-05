"""
Sincronizare nocturnă (cron): pull structură Airtable → Django pe toată baza.

Punct de intrare STABIL pentru cron-ul Railway — comportamentul se ajustează
aici, în cod, fără a schimba configurarea Railway. Rulează pull-ul pe toate
grupele active, creând conturile de profesor lipsă, și arhivând ce a dispărut.

Cron Railway (start command):
    python manage.py nightly_sync

Necesită AIRTABLE_TOKEN (read) în mediu. Idempotent: se poate rula oricând.
"""
from django.core.management.base import BaseCommand, CommandError

from crm_sync.airtable_client import AirtableConfigError
from crm_sync.pull_sync import PullSync


class Command(BaseCommand):
    help = "Sincronizare nocturnă: pull structură din Airtable (toată baza)."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help="Nu scrie nimic; doar raportează.")
        parser.add_argument('--no-create-teachers', action='store_true',
                            help="Nu crea conturi noi de profesor pentru cei nepotriviți.")

    def handle(self, *args, **opts):
        try:
            sync = PullSync(
                dry_run=opts['dry_run'], grupa=None, log=self.stdout.write,
                create_missing_teachers=not opts['no_create_teachers'],
            )
            result = sync.run()
        except AirtableConfigError as exc:
            raise CommandError(str(exc))

        t = result['totals']
        style = self.style.SUCCESS if result['status'] in ('success', 'dry_run') else self.style.WARNING
        self.stdout.write(style(
            f"\nSync nocturn [{result['status']}] — create: {t['created']}, "
            f"actualizate: {t['updated']}, arhivate: {t['archived']}, "
            f"sărite: {t['skipped']}, erori: {t['errors']}."))
        if result['errors']:
            for e in result['errors'][:10]:
                self.stdout.write(self.style.ERROR(f"  - {e}"))
