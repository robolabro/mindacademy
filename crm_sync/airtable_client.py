"""
Client REST minim pentru Airtable, construit peste pyairtable.

pyairtable apelează REST API-ul Airtable și se ocupă nativ de:
  - paginare (`.all()` parcurge toate paginile),
  - rate limiting (5 req/s per bază),
  - retry cu backoff pe 429 (retry_strategy).

Tokenul (PAT) se citește DOAR din setări/mediu — niciodată din cod. Scope-ul
recomandat al tokenului: doar baza `AIRTABLE_BASE_ID`, doar tabelele folosite,
`data.records:read` (+ `data.records:write` pentru push-ul din Faza 4).
"""
from django.conf import settings


class AirtableConfigError(RuntimeError):
    """Configurare Airtable lipsă/incompletă (token sau bază)."""


def _require(name):
    value = getattr(settings, name, '') or ''
    if not value:
        raise AirtableConfigError(
            f"{name} lipsește. Setează variabila de mediu (PAT-ul Airtable NU "
            f"se pune în cod/git)."
        )
    return value


def get_api():
    """Returnează un client pyairtable.Api autentificat cu PAT-ul din mediu."""
    from pyairtable import Api  # import întârziat: nu forța dependința la load
    token = _require('AIRTABLE_TOKEN')
    # pyairtable reîncearcă automat pe 429 și respectă rate limit-ul de 5 req/s.
    return Api(token, timeout=(10, 30))


def get_table(table_id, base_id=None):
    """Returnează un handle de tabel pentru `table_id` din baza configurată."""
    base_id = base_id or _require('AIRTABLE_BASE_ID')
    return get_api().table(base_id, table_id)


def fetch_all(table_id, base_id=None, **options):
    """
    Ia toate înregistrările dintr-un tabel (parcurgând paginile).
    Fiecare înregistrare are forma pyairtable: {'id': 'rec...', 'fields': {...},
    'createdTime': ...}. `options` se transmit către `.all()` (ex: formula=...,
    fields=[...], page_size=100).
    """
    return get_table(table_id, base_id).all(**options)
