import os
import shutil
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import AnalysisJob


@admin.register(AnalysisJob)
class AnalysisJobAdmin(admin.ModelAdmin):
    list_display = [
        'original_filename', 'file_size_display', 'status_badge',
        'n_cells', 'n_clusters', 'created_at', 'view_link'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['original_filename']
    ordering = ['-created_at']

    @admin.display(description='Size')
    def file_size_display(self, obj):
        try:
            size = obj.file.size
            if size < 1024: return f"{size} B"
            elif size < 1024*1024: return f"{size/1024:.1f} KB"
            return f"{size/(1024*1024):.1f} MB"
        except Exception:
            return '—'

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'pending': '#6c757d', 'running': '#ffc107',
            'completed': '#28a745', 'failed': '#dc3545'
        }
        return format_html(
            '<span style="display:inline-block;padding:2px 10px;border-radius:12px;'
            'background:{};color:#fff;font-size:.8rem;font-weight:600;">{}</span>',
            colors.get(obj.status, '#6c757d'), obj.get_status_display()
        )

    @admin.display(description='View')
    def view_link(self, obj):
        url = reverse('analysis_result', args=[obj.id])
        return format_html('<a href="{}" target="_blank">View →</a>', url)

    # Custom actions (no @admin.action decorator for compatibility)
    def delete_with_files(self, request, queryset):
        count = 0
        for job in queryset:
            d = job.result_dir()
            if d.exists(): shutil.rmtree(d)
            if job.file: job.file.delete(save=False)
            job.delete()
            count += 1
        self.message_user(request, f'Deleted {count} jobs + files.')
    delete_with_files.short_description = '🗑️ Delete selected jobs + all files'

    def cleanup_failed(self, request, queryset):
        failed = AnalysisJob.objects.filter(status='failed')
        count = 0
        for job in failed:
            d = job.result_dir()
            if d.exists(): shutil.rmtree(d)
            if job.file: job.file.delete(save=False)
            job.delete()
            count += 1
        self.message_user(request, f'Cleaned up {count} failed jobs.')
    cleanup_failed.short_description = '🧹 Clean up all failed jobs'

    actions = [delete_with_files, cleanup_failed]
