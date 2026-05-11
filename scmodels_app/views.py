import markdown
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.utils.safestring import mark_safe
from .models import ModelEntry, Tag
from .models_resources import ResourceCategory, Resource


def index(request):
    """Portal homepage — grid of all resource categories."""
    query = request.GET.get('q', '')

    categories = ResourceCategory.objects.filter(is_active=True)
    model_entries = ModelEntry.objects.filter(published=True)

    if query:
        model_entries = model_entries.filter(
            Q(name__icontains=query)
            | Q(short_description__icontains=query)
            | Q(authors__icontains=query)
            | Q(tags__name__icontains=query)
        ).distinct()

    return render(request, 'scmodels_app/portal.html', {
        'categories': categories,
        'model_entries': model_entries,
        'query': query,
    })


def scmodel_list(request):
    """Full scModel listing (category 1 detail)."""
    query = request.GET.get('q', '')
    model_type = request.GET.get('type', '')
    tag_name = request.GET.get('tag', '')

    entries = ModelEntry.objects.filter(published=True)

    if query:
        entries = entries.filter(
            Q(name__icontains=query)
            | Q(short_description__icontains=query)
            | Q(authors__icontains=query)
            | Q(tags__name__icontains=query)
        ).distinct()
    if model_type:
        entries = entries.filter(model_type=model_type)
    if tag_name:
        entries = entries.filter(tags__name=tag_name)

    all_tags = Tag.objects.all()
    model_types = ModelEntry.MODEL_TYPE_CHOICES

    return render(request, 'scmodels_app/scmodel_list.html', {
        'entries': entries,
        'all_tags': all_tags,
        'model_types': model_types,
        'query': query,
        'current_type': model_type,
        'current_tag': tag_name,
    })


def scmodel_detail(request, slug):
    entry = get_object_or_404(ModelEntry, slug=slug, published=True)
    # Render markdown description to HTML
    if entry.description:
        # Protect inline math ($...$) and display math ($$...$$) from markdown processing
        import re
        text = entry.description
        math_blocks = []
        # Protect $$...$$ display math first
        def save_display(m):
            math_blocks.append(m.group(0))
            return f'⧸⧸MATH{len(math_blocks)-1}MATH⧸⧸'
        text = re.sub(r'\$\$[^$]+\$\$', save_display, text)
        # Protect $...$ inline math
        def save_inline(m):
            math_blocks.append(m.group(0))
            return f'⧸MATH{len(math_blocks)-1}MATH⧸'
        text = re.sub(r'\$[^$]+\$', save_inline, text)

        md_html = markdown.markdown(
            text,
            extensions=['fenced_code', 'tables', 'nl2br']
        )
        # Restore math blocks
        for i, block in enumerate(math_blocks):
            md_html = md_html.replace(f'⧸⧸MATH{i}MATH⧸⧸', block)
            md_html = md_html.replace(f'⧸MATH{i}MATH⧸', block)

        entry.description_html = mark_safe(md_html)
    else:
        entry.description_html = ''
    return render(request, 'scmodels_app/scmodel_detail.html', {'entry': entry})


def resource_category(request, slug):
    """Category detail — list resources in this category.
    For scmodel, delegate to scmodel_list."""
    if slug == 'scmodel':
        return scmodel_list(request)

    category = get_object_or_404(ResourceCategory, slug=slug, is_active=True)
    resources = category.resources.filter(is_active=True)

    return render(request, 'scmodels_app/category_detail.html', {
        'category': category,
        'resources': resources,
    })
