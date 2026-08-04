from django.apps import AppConfig


class CrmSyncConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crm_sync'
    verbose_name = "Sincronizare CRM (Airtable)"
