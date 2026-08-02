"""
Sincronizează curriculumul din Airtable în Django.

Utilizare:
    python manage.py sync_curriculum            # sincronizează
    python manage.py sync_curriculum --dry-run  # doar raportează, nu scrie

Necesită în .env / mediu:
    AIRTABLE_TOKEN   = Personal Access Token cu acces la bază
    AIRTABLE_BASE_ID = id-ul bazei cu tabelul Module (ex: app...)
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from courses.curriculum_sync import fetch_airtable_records, upsert_curriculum


class Command(BaseCommand):
    help = "Sincronizează curriculumul (Course/Module/LessonTemplate) din Airtable."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help="Raportează ce s-ar schimba, fără a scrie în DB.")

    def handle(self, *args, **options):
        token = getattr(settings, 'AIRTABLE_TOKEN', '')
        base_id = getattr(settings, 'AIRTABLE_BASE_ID', '')
        if not token or not base_id:
            raise CommandError(
                "Lipsesc AIRTABLE_TOKEN și/sau AIRTABLE_BASE_ID în configurare "
                "(.env sau variabile de mediu)."
            )

        dry = options['dry_run']
        self.stdout.write(self.style.WARNING(
            "DRY-RUN — nu se scrie nimic\n" if dry else "Sincronizez curriculumul...\n"))

        try:
            courses, modules, lessons = fetch_airtable_records(token, base_id)
        except ImportError:
            raise CommandError("pyairtable nu este instalat. Rulează: pip install pyairtable")
        except Exception as exc:  # erori de rețea / schemă
            raise CommandError(f"Eroare la citirea din Airtable: {exc}")

        self.stdout.write(
            f"Aduse din Airtable: {len(courses)} cursuri, "
            f"{len(modules)} module, {len(lessons)} lecții.\n")

        stats = upsert_curriculum(courses, modules, lessons,
                                  dry_run=dry, log=self.stdout.write)

        self.stdout.write(self.style.SUCCESS(
            "\nGata. "
            f"Cursuri: +{stats['courses'][0]}/~{stats['courses'][1]}  ·  "
            f"Module: +{stats['modules'][0]}/~{stats['modules'][1]}  ·  "
            f"Lecții: +{stats['lessons'][0]}/~{stats['lessons'][1]}"
            + ("  (dry-run, nimic salvat)" if dry else "")))
