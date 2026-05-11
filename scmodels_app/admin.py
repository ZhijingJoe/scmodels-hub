from django.contrib import admin
from .models import ModelEntry, Tag, ResourceCategory, Resource


@admin.register(ModelEntry)
class ModelEntryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'model_type', 'modality', 'featured',
        'published', 'publication_date', 'created_at'
    ]
    list_filter = ['model_type', 'modality', 'featured', 'published', 'tags']
    search_fields = ['name', 'short_description', 'authors', 'paper_title']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['tags']
    fieldsets = (
        ('Basic', {
            'fields': ('name', 'slug', 'short_description', 'description')
        }),
        ('Paper', {
            'fields': ('paper_title', 'paper_url', 'paper_doi',
                       'authors', 'publication_date', 'journal')
        }),
        ('Links', {
            'fields': ('github_url', 'website_url', 'huggingface_url',
                       'wechat_article_url', 'wechat_article_title')
        }),
        ('Classification', {
            'fields': ('model_type', 'modality', 'tags')
        }),
        ('Technical Specs', {
            'fields': ('architecture', 'pretraining_data',
                       'parameter_count', 'embedding_dim', 'context_length')
        }),
        ('Display', {
            'fields': ('cover_image', 'thumbnail_url', 'featured', 'published')
        }),
    )


@admin.register(ResourceCategory)
class ResourceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'sort_order', 'is_active']
    list_editable = ['sort_order', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    fields = ['name', 'slug', 'description', 'icon', 'background_image', 'sort_order', 'is_active']


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'sort_order', 'is_active']
    list_filter = ['category', 'is_active']
    list_editable = ['sort_order', 'is_active']
    search_fields = ['title', 'url']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
