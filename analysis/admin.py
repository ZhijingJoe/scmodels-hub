from django.contrib import admin
from .models import AnalysisJob


@admin.register(AnalysisJob)
class AnalysisJobAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'status', 'n_cells', 'n_clusters', 'created_at']
    list_filter = ['status']
    readonly_fields = ['id', 'status', 'error_message', 'n_cells', 'n_genes', 'n_clusters']
