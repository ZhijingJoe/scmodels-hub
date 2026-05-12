import uuid
from django.db import models
from django.conf import settings


class AnalysisJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='analysis/uploads/')
    original_filename = models.CharField(max_length=300)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)

    # Analysis parameters
    min_genes = models.IntegerField(default=200, help_text='Min genes per cell')
    min_cells = models.IntegerField(default=3, help_text='Min cells per gene')
    n_top_genes = models.IntegerField(default=2000, help_text='HVGs')
    n_neighbors = models.IntegerField(default=15)
    resolution = models.FloatField(default=0.8)
    n_markers = models.IntegerField(default=10, help_text='Top markers per cluster')

    # Results metadata
    n_cells = models.IntegerField(null=True, blank=True)
    n_genes = models.IntegerField(null=True, blank=True)
    n_clusters = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def result_dir(self):
        return settings.MEDIA_ROOT / 'analysis' / 'results' / str(self.id)

    def result_url(self, filename):
        return f"{settings.MEDIA_URL}analysis/results/{self.id}/{filename}"
