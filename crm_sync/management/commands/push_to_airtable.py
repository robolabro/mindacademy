"""
Comandă: push Django → Airtable (Epic 7, Faza 4).

Împinge prezențele + lecțiile finalizate în Airtable (NU în „Progres Lectii").

Exemple:
    # Simulare pe o grupă (nimic nu se scrie):
    python manage.py push_to_airtable --grupa=COD --dry-run

    # Push real pe grupa pilot:
    python manage.py push_to_airtable --grupa=COD

Necesită AIRTABLE_TOKEN cu scope data.records:write pe baza configurată.
"""
from django.core.management.base import BaseCommand, CommandError

from crm_sync.airtable_client import AirtableConfigError
from crm_sync.push_sync import PushSync


class Command(BaseCommand):
    help = "Împinge execuția (prezențe + lecție finalizată) din Django în Airtable."

    def add_arguments(self, parser):
        parser.add_argument('--grupa', default=None,
                            help="Cod Grupa: restrânge la o singură grupă (pilot).")
        parser.add_argument('--dry-run', action='store_true',
                            help="Nu scrie nimic; doar raportează ce s-ar trimite.")

    def handle(self, *args, **opts):
        grupa = opts['grupa']
        dry_run = opts['dry_run']
        if not grupa and not dry_run:
            self.stdout.write(self.style.WARNING(
                "Push pe TOATE grupele fără --grupa. Pilotează întâi pe o grupă "
                "(--grupa=COD)."))
        try:
            push = PushSync(dry_run=dry_run, grupa=grupa, log=self.stdout.write)
            result = push.run()
        except AirtableConfigError as exc:
            raise CommandError(str(exc))

        t = result['totals']
        style = self.style.SUCCESS if result['status'] in ('success', 'dry_run') else self.style.WARNING
        self.stdout.write(style(
            f"\nGata [{result['status']}] — create: {t['created']}, "
            f"actualizate: {t['updated']}, sărite: {t['skipped']}, erori: {t['errors']}."))
        for e in result['errors'][:10]:
            self.stdout.write(self.style.ERROR(f"  - {e}"))
