"""
Modele partajate pentru sincronizarea bidirecțională Airtable ↔ Mind.academy.

Principiu de bază (Epic 7):
  - Airtable = sursa de adevăr pentru STRUCTURĂ (grupe, module, lecții-template,
    elevi, înscrieri, lecții programate)  → se face PULL în Django.
  - Mind.academy = sursa de adevăr pentru EXECUȚIE (prezențe, lecție finalizată,
    rezultate)  → se face PUSH în Airtable.

`AirtableSyncMixin` este o clasă abstractă: fiecare model concret care o
moștenește primește propriile coloane de mapare. Cheia de upsert este
ÎNTOTDEAUNA `airtable_record_id` (niciodată numele — copiii pot avea nume
identice). Ștergerile din Airtable nu se propagă ca DELETE în Django; se
marchează `is_archived=True`.
"""
from django.db import models
from django.utils import timezone


class AirtableSyncMixin(models.Model):
    """
    Câmpuri de mapare/urmărire adăugate modelelor sincronizate cu Airtable.
    Abstract — nu creează tabel propriu.
    """
    SYNC_STATUS_CHOICES = [
        ('pending', 'În așteptare'),
        ('synced', 'Sincronizat'),
        ('error', 'Eroare'),
    ]

    # Cheia de mapare cu Airtable — recID-ul înregistrării sursă.
    # Poate fi gol pentru înregistrări create în Django care nu există (încă)
    # în Airtable. Unic (per model) atunci când e completat.
    airtable_record_id = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        unique=True,
        db_index=True,
        verbose_name="Airtable Record ID",
        help_text="ID-ul înregistrării din Airtable (recXXXXXXXXXXXXXX). Cheie de upsert."
    )

    airtable_synced_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Ultima sincronizare"
    )
    sync_status = models.CharField(
        max_length=20,
        choices=SYNC_STATUS_CHOICES,
        default='pending',
        verbose_name="Status sincronizare"
    )
    sync_error = models.TextField(
        blank=True,
        verbose_name="Ultima eroare de sincronizare"
    )

    # Marcat True când înregistrarea a dispărut din Airtable (nu ștergem
    # niciodată automat — arhivăm).
    is_archived = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Arhivat (dispărut din Airtable)"
    )

    class Meta:
        abstract = True

    def mark_synced(self, save=True):
        """Marchează înregistrarea ca sincronizată cu succes acum."""
        self.airtable_synced_at = timezone.now()
        self.sync_status = 'synced'
        self.sync_error = ''
        if save:
            self.save(update_fields=[
                'airtable_synced_at', 'sync_status', 'sync_error'
            ])

    def mark_sync_error(self, message, save=True):
        """Înregistrează o eroare de sincronizare pe această înregistrare."""
        self.sync_status = 'error'
        self.sync_error = str(message)[:2000]
        if save:
            self.save(update_fields=['sync_status', 'sync_error'])


class SyncLog(models.Model):
    """
    Jurnal al rulărilor de sincronizare (pull sau push). Fiecare rulare a unei
    comenzi de management scrie un rând aici pentru audit și depanare.
    """
    DIRECTION_CHOICES = [
        ('pull', 'Airtable → Django'),
        ('push', 'Django → Airtable'),
    ]
    STATUS_CHOICES = [
        ('running', 'În curs'),
        ('success', 'Succes'),
        ('partial', 'Parțial (cu erori)'),
        ('error', 'Eroare'),
        ('dry_run', 'Simulare (dry-run)'),
    ]

    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES,
                                 verbose_name="Direcție")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES,
                              default='running', verbose_name="Status")

    # Domeniul rulării (ex: cod grupă pilot, sau 'all')
    scope = models.CharField(max_length=100, blank=True, verbose_name="Domeniu")
    dry_run = models.BooleanField(default=False, verbose_name="Simulare")

    # Contoare rezumat
    records_created = models.PositiveIntegerField(default=0, verbose_name="Create")
    records_updated = models.PositiveIntegerField(default=0, verbose_name="Actualizate")
    records_archived = models.PositiveIntegerField(default=0, verbose_name="Arhivate")
    records_skipped = models.PositiveIntegerField(default=0, verbose_name="Sărite")
    errors_count = models.PositiveIntegerField(default=0, verbose_name="Erori")

    # Detalii libere (rezumat text sau JSON serializat)
    details = models.TextField(blank=True, verbose_name="Detalii")

    started_at = models.DateTimeField(default=timezone.now, verbose_name="Pornit la")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="Terminat la")

    class Meta:
        verbose_name = "Jurnal Sincronizare"
        verbose_name_plural = "Jurnale Sincronizare"
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.get_direction_display()} · {self.get_status_display()} · {self.started_at:%d.%m.%Y %H:%M}"


class AirtablePushJob(models.Model):
    """
    Coadă de scrieri Django → Airtable (execuție).

    Modelul de execuție (prezențe, lecție finalizată) generează un job aici;
    comanda de push îl procesează prin REST API și marchează rezultatul.
    Astfel scrierile în Airtable sunt idempotente, reluabile și auditabile,
    fără a bloca fluxul din interfața profesorului.
    """
    STATUS_CHOICES = [
        ('pending', 'În așteptare'),
        ('done', 'Trimis'),
        ('error', 'Eroare'),
        ('skipped', 'Sărit'),
    ]

    # Ce entitate Airtable țintim: tabelul + (opțional) recordul existent.
    target_table = models.CharField(max_length=100, verbose_name="Tabel Airtable")
    target_record_id = models.CharField(
        max_length=64, blank=True,
        verbose_name="Record ID țintă",
        help_text="recID existent (update). Gol dacă e create."
    )

    # Payload-ul de câmpuri de scris (doar câmpuri editabile — niciodată
    # formula/lookup/rollup/count).
    payload = models.JSONField(default=dict, verbose_name="Payload câmpuri")

    # Legătura către obiectul Django sursă, ca după un CREATE să scriem
    # record-id-ul Airtable înapoi pe el (idempotență la rulările următoare).
    SOURCE_CHOICES = [
        ('prezenta', 'Prezență'),
        ('lectie', 'Lecție finalizată'),
    ]
    source_kind = models.CharField(max_length=20, choices=SOURCE_CHOICES, blank=True,
                                   verbose_name="Tip sursă")
    source_id = models.PositiveIntegerField(null=True, blank=True,
                                            verbose_name="ID obiect Django sursă")
    # Cheie de deduplicare: un singur job „pending" per sursă.
    dedupe_key = models.CharField(max_length=64, blank=True, db_index=True,
                                  verbose_name="Cheie deduplicare")

    status = models.CharField(max_length=10, choices=STATUS_CHOICES,
                              default='pending', db_index=True, verbose_name="Status")
    attempts = models.PositiveIntegerField(default=0, verbose_name="Încercări")
    last_error = models.TextField(blank=True, verbose_name="Ultima eroare")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creat la")
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="Procesat la")

    class Meta:
        verbose_name = "Job Push Airtable"
        verbose_name_plural = "Joburi Push Airtable"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.target_table} · {self.get_status_display()} · {self.created_at:%d.%m.%Y %H:%M}"
