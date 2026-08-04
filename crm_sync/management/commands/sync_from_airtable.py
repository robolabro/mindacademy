"""
Comandă: pull Airtable → Django (Epic 7, Faza 2).

Exemple:
    # 1) Descoperă numele reale ale câmpurilor (nimic nu se scrie):
    python manage.py sync_from_airtable --show-schema

    # 2) Simulare pe o singură grupă (pilot obligatoriu, nimic în DB):
    python manage.py sync_from_airtable --grupa=COD --dry-run

    # 3) Rulare reală pe grupa pilot:
    python manage.py sync_from_airtable --grupa=COD

    # 4) Rulare pe toată baza (după ce pilotul a fost validat):
    python manage.py sync_from_airtable

Tokenul (AIRTABLE_TOKEN) se citește din mediu — niciodată din cod.
"""
from django.core.management.base import BaseCommand, CommandError

from crm_sync.airtable_client import AirtableConfigError
from crm_sync.pull_sync import PullSync, show_schema


class Command(BaseCommand):
    help = "Sincronizează structura din Airtable în Django (pull, read-only în Airtable)."

    def add_arguments(self, parser):
        parser.add_argument('--grupa', default=None,
                            help="Cod Grupa: restrânge sincronizarea la o singură grupă (pilot).")
        parser.add_argument('--dry-run', action='store_true',
                            help="Nu scrie nimic în DB; doar raportează ce s-ar întâmpla.")
        parser.add_argument('--show-schema', action='store_true',
                            help="Tipărește numele câmpurilor din fiecare tabel și iese.")
        parser.add_argument('--create-missing-teachers', action='store_true',
                            help="Creează conturi de profesor pentru cei din Airtable "
                                 "care nu se potrivesc cu niciun profesor Django "
                                 "(implicit: doar potrivire, fără creare).")

    def handle(self, *args, **opts):
        try:
            if opts['show_schema']:
                show_schema(log=self.stdout.write)
                return

            grupa = opts['grupa']
            dry_run = opts['dry_run']

            if not grupa and not dry_run:
                self.stdout.write(self.style.WARNING(
                    "Rulezi pe TOATĂ baza fără --grupa. Pilotul pe o singură "
                    "grupă (--grupa=COD) trebuie validat înainte. Continui doar "
                    "dacă ești sigur."))

            sync = PullSync(dry_run=dry_run, grupa=grupa, log=self.stdout.write,
                            create_missing_teachers=opts['create_missing_teachers'])
            result = sync.run()

            t = result['totals']
            style = self.style.SUCCESS if result['status'] in ('success', 'dry_run') \
                else self.style.WARNING
            self.stdout.write(style(
                f"\nGata [{result['status']}] — create: {t['created']}, "
                f"actualizate: {t['updated']}, arhivate: {t['archived']}, "
                f"sărite: {t['skipped']}, erori: {t['errors']}."))
            if result['errors']:
                self.stdout.write(self.style.ERROR(
                    f"{len(result['errors'])} erori (primele 10):"))
                for e in result['errors'][:10]:
                    self.stdout.write(f"  - {e}")
        except AirtableConfigError as exc:
            raise CommandError(str(exc))
