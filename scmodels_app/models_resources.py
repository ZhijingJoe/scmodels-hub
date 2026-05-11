from django.db import models


class ResourceCategory(models.Model):
    """Top-level resource category (e.g. Datasets, CNS Papers, Teams...)"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.CharField(max_length=300, blank=True)
    icon = models.CharField(
        max_length=10, blank=True,
        help_text='Single emoji for the category card'
    )
    background_image = models.ImageField(
        upload_to='categories/backgrounds/', blank=True, null=True,
        help_text='Full-width background image for the category detail page'
    )
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'Resource Categories'

    def __str__(self):
        return self.name


class Resource(models.Model):
    """A single resource link within a category."""
    category = models.ForeignKey(
        ResourceCategory, on_delete=models.CASCADE, related_name='resources'
    )
    title = models.CharField(max_length=300)
    url = models.URLField(max_length=1000)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'sort_order', 'title']

    def __str__(self):
        return f"[{self.category.name}] {self.title}"
