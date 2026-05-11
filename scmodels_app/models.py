from django.db import models
from django.utils.text import slugify
from django.utils.html import mark_safe
from .models_resources import ResourceCategory, Resource


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ModelEntry(models.Model):
    MODEL_TYPE_CHOICES = [
        ('foundation', 'Foundation Model'),
        ('geneformer', 'Geneformer-like'),
        ('virtual_cell', 'Virtual Cell'),
        ('multimodal', 'Multi-modal'),
        ('spatial', 'Spatial'),
        ('perturbation', 'Perturbation'),
        ('generative', 'Generative'),
        ('other', 'Other'),
    ]

    MODALITY_CHOICES = [
        ('scrna', 'scRNA-seq'),
        ('scatac', 'scATAC-seq'),
        ('multiome', 'Multiome'),
        ('spatial', 'Spatial'),
        ('citeseq', 'CITE-seq'),
        ('other', 'Other'),
    ]

    # Basic info
    name = models.CharField(max_length=200, help_text='Model/Project name')
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    short_description = models.CharField(
        max_length=300, help_text='One-line summary for listing cards'
    )
    description = models.TextField(help_text='Detailed description (Markdown)')
    
    # Paper
    paper_title = models.CharField(max_length=500, blank=True)
    paper_url = models.URLField(blank=True, help_text='arXiv / journal URL')
    paper_doi = models.CharField(max_length=100, blank=True)
    authors = models.TextField(blank=True, help_text='Comma-separated')
    publication_date = models.DateField(null=True, blank=True)
    journal = models.CharField(max_length=200, blank=True)

    # Links
    github_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)
    huggingface_url = models.URLField(blank=True)
    wechat_article_url = models.URLField(
        blank=True, help_text='Link to WeChat public account科普推文 (mp.weixin.qq.com)'
    )
    wechat_article_title = models.CharField(
        max_length=300, blank=True, help_text='Display title for the WeChat article link'
    )

    # Taxonomy
    model_type = models.CharField(
        max_length=20, choices=MODEL_TYPE_CHOICES, default='other'
    )
    modality = models.CharField(
        max_length=20, choices=MODALITY_CHOICES, default='scrna'
    )
    tags = models.ManyToManyField(Tag, blank=True)

    # Technical specs
    architecture = models.CharField(max_length=200, blank=True)
    pretraining_data = models.CharField(
        max_length=500, blank=True, help_text='Pretraining datasets used'
    )
    parameter_count = models.CharField(
        max_length=50, blank=True, help_text='e.g. "300M", "6.5B"'
    )
    embedding_dim = models.IntegerField(null=True, blank=True)
    context_length = models.IntegerField(
        null=True, blank=True, help_text='Max input tokens/cells'
    )

    # Display
    thumbnail_url = models.URLField(blank=True, help_text='Optional figure/image URL')
    cover_image = models.ImageField(
        upload_to='models/covers/', blank=True, null=True,
        help_text='Upload a cover image (shown on detail page and card)'
    )
    featured = models.BooleanField(default=False)
    published = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-publication_date', '-created_at']
        verbose_name_plural = 'Model Entries'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
