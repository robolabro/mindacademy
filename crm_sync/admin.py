from django.contrib import admin
from .models import SyncLog, AirtablePushJob


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ['started_at', 'direction', 'status', 'scope', 'dry_run',
                    'records_created', 'records_updated', 'records_archived',
                    'errors_count', 'finished_at']
    list_filter = ['direction', 'status', 'dry_run']
    search_fields = ['scope', 'details']
    readonly_fields = ['started_at', 'finished_at']
    date_hierarchy = 'started_at'


@admin.register(AirtablePushJob)
class AirtablePushJobAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'source_kind', 'target_table', 'target_record_id',
                    'status', 'attempts', 'processed_at']
    list_filter = ['status', 'source_kind', 'target_table']
    search_fields = ['target_record_id', 'dedupe_key', 'last_error']
    readonly_fields = ['created_at', 'processed_at']
    date_hierarchy = 'created_at'
