"""
Client REST de SCRIERE în Airtable (Epic 7, Faza 4), peste pyairtable.

Scriem DOAR câmpuri editabile (checkbox, text, linked-record) — niciodată
formula/lookup/rollup/count. Tokenul (PAT) trebuie să aibă scope
`data.records:write` pe baza configurată.

Nu scriem NICIODATĂ în tabelul „Progres Lectii" — acela e generat de o
automatizare Airtable pe baza Prezențelor cu Attended=true.
"""
from django.conf import settings

from crm_sync.airtable_client import get_table

# Tabelul interzis la scriere (generat de automatizarea Airtable).
FORBIDDEN_TABLES = set()


def _forbidden():
    return {getattr(settings, 'AIRTABLE_TABLE_PROGRES_LECTII', '')}


def create_record(table_id, fields):
    """Creează o înregistrare în `table_id`. Returnează dict pyairtable
    ({'id': 'rec...', 'fields': {...}})."""
    if table_id in _forbidden():
        raise ValueError("Scriere interzisă în Progres Lectii (generat de automatizarea Airtable).")
    return get_table(table_id).create(fields)


def update_record(table_id, record_id, fields):
    """Actualizează o înregistrare existentă. Returnează dict pyairtable."""
    if table_id in _forbidden():
        raise ValueError("Scriere interzisă în Progres Lectii (generat de automatizarea Airtable).")
    return get_table(table_id).update(record_id, fields)


def delete_record(table_id, record_id):
    """Șterge o înregistrare (folosit doar pentru curățarea duplicatelor pe
    care le-am creat noi). Operațiune ireversibilă."""
    if table_id in _forbidden():
        raise ValueError("Ștergere interzisă în Progres Lectii (generat de automatizarea Airtable).")
    return get_table(table_id).delete(record_id)
