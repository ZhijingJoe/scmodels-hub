import os
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
    readonly_fields = [
        'id', 'status', 'error_message', 'n_cells', 'n_genes',
        'n_clusters', 'created_at', 'updated_at',
        'file_download', 'result_files', 'parameters_summary'
    ]
    fieldsets = (
        ('Job Info', {
            'fields': ('id', 'original_filename', 'status', 'error_message')
        }),
        ('File', {
            'fields': ('file', 'file_download')
        }),
        ('Parameters', {
            'fields': ('parameters_summary',)
        }),
        ('Results', {
            'fields': ('n_cells', 'n_genes', 'n_clusters', 'result_files')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    actions = ['delete_with_files', 'cleanup_failed']

    @admin.display(description='Size')
    def file_size_display(self, obj):
        try:
            size = obj.file.size
            if size < 1024: return f"{size} B"
            elif size < 1024*1024: return f"{size/1024:.1f} KB"
            else: return f"{size/(1024*1024):.1f} MB"
        except: return '—'

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

    @admin.display(description='Download')
    def file_download(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" download>📥 Download {}</a>',
                obj.file.url, os.path.basename(obj.file.name)
            )
        return '—'

    @admin.display(description='Result Plots')
    def result_files(self, obj):
        if obj.status != 'completed':
            return '—'
        result_dir = obj.result_dir()
        if not result_dir.exists():
            return 'No results'
        links = []
        for ext in ['.png', '.csv']:
            for f in sorted(result_dir.glob(f'*{ext}')):
                rel = str(f.relative_to(result_dir))
                url = obj.result_url(rel)
                links.append(f'<a href="{url}" target="_blank">{rel}</a>')
        return format_html('<br>'.join(links)) if links else '—'

    @admin.display(description='Parameters')
    def parameters_summary(self, obj):
        return format_html(
            'min_genes={} / min_cells={} / n_top_genes={}<br>'
            'n_neighbors={} / resolution={} / n_markers={}',
            obj.min_genes, obj.min_cells, obj.n_top_genes,
            obj.n_neighbors, obj.resolution, obj.n_markers
        )

    @admin.display(description='View')
    def view_link(self, obj):
        result_url = reverse('analysis_result', args=[obj.id])
        return format_html(
            '<a href="{}" target="_blank">View</a>',
            result_url
        )

    @admin.action(description='🗑️ Delete selected jobs + all files')
    def delete_with_files(self, request, queryset):
        count = 0
        for job in queryset:
            # Delete result directory
            result_dir = job.result_dir()
            if result_dir.exists():
                import shutil
                shutil.rmtree(result_dir)
            # Delete uploaded file
            if job.file:
                job.file.delete(save=False)
            job.delete()
            count += 1
        self.message_user(request, f'Deleted {count} jobs and all associated files.')

    @admin.action(description='🧹 Clean up all failed jobs')
    def cleanup_failed(self, request, queryset):
        failed = AnalysisJob.objects.filter(status='failed')
        count = failed.count()
        for job in failed:
            result_dir = job.result_dir()
            if result_dir.exists():
                import shutil
                shutil.rmtree(result_dir)
            if job.file:
                job.file.delete(save=False)
            job.delete()
        self.message_user(request, f'Cleaned up {count} failed jobs.')
