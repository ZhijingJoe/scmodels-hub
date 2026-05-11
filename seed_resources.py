import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from scmodels_app.models_resources import ResourceCategory, Resource

# ── 10 Categories ──
categories = [
    (1, "scModel", "scmodel",
     "Large AI models for single-cell biology — foundation models, virtual cells, geneformers.",
     "🧬"),
    (2, "Single-Cell Datasets", "datasets",
     "Large-scale single-cell reference datasets: CELLxGENE, Tahoe-100M, scBaseCount, and more.",
     "📊"),
    (3, "Dataset Tutorials", "dataset-tutorials",
     "Guides and tutorials for accessing, processing, and analyzing major single-cell datasets.",
     "📖"),
    (4, "CNS Atlas Papers", "cns-atlas-papers",
     "Recent single-cell atlas papers from CNS journals (Cell, Nature, Science) and major sub-journals.",
     "📄"),
    (5, "Analysis Methods", "analysis-methods",
     "Common single-cell analysis workflows, pipelines, and computational methods.",
     "🔬"),
    (6, "Key Research Teams", "key-teams",
     "Leading research groups and institutes pushing single-cell AI forward.",
     "🏛️"),
    (7, "Single-Cell Agents", "sc-agents",
     "AI agents for single-cell data analysis, literature mining, and experimental design.",
     "🤖"),
    (8, "Multi-Omics Atlases", "multiomics-atlases",
     "Integrated single-cell multi-omics atlases and cross-modality mapping resources.",
     "🧩"),
    (9, "Spatial Transcriptomics", "spatial-transcriptomics",
     "Spatial transcriptomics technologies, benchmarks, and analytical advances.",
     "🗺️"),
    (10, "Atlas Consortia", "atlas-consortia",
     "Large-scale collaborative atlas projects: Human Cell Atlas, BICCN, HuBMAP, and more.",
     "🌍"),
]

for sort, name, slug, desc, icon in categories:
    cat, created = ResourceCategory.objects.get_or_create(
        slug=slug,
        defaults={'name': name, 'description': desc, 'icon': icon, 'sort_order': sort}
    )
    status = "+" if created else "="
    print(f"  {status} [{sort}] {name}")

# ── Seed resources for selected categories ──
resources_data = {
    "datasets": [
        ("CELLxGENE Census", "https://cellxgene.cziscience.com/"),
        ("Tahoe-100M", "https://github.com/related-sciences/tahoe-100m"),
        ("scBaseCount", "https://scbasecount.readthedocs.io/"),
        ("Human Cell Atlas Data Portal", "https://data.humancellatlas.org/"),
        ("Single Cell Portal (Broad)", "https://singlecell.broadinstitute.org/"),
        ("PanglaoDB", "https://panglaodb.se/"),
        ("Tabula Sapiens", "https://tabula-sapiens-portal.ds.czbiohub.org/"),
        ("DISCO", "https://www.immunesinglecell.org/"),
    ],
    "dataset-tutorials": [
        ("CELLxGENE Census Python API Guide", "https://chanzuckerberg.github.io/cellxgene-census/"),
        ("Scanpy Tutorials", "https://scanpy.readthedocs.io/en/stable/tutorials.html"),
        ("Seurat Vignettes", "https://satijalab.org/seurat/articles/"),
        ("Single Cell Best Practices", "https://www.sc-best-practices.org/"),
    ],
    "key-teams": [
        ("Arc Institute", "https://arcinstitute.org/"),
        ("CZ Biohub — Quake Lab", "https://www.czbiohub.org/"),
        ("Broad Institute — Regev Lab", "https://www.broadinstitute.org/"),
        ("Stanford — Leskovec Lab", "https://snap.stanford.edu/"),
        ("Helmholtz Munich — Theis Lab", "https://www.helmholtz-munich.de/"),
        ("Wellcome Sanger Institute", "https://www.sanger.ac.uk/"),
        ("BGI Research — scFoundation Team", "https://github.com/biomap-research/scFoundation"),
        ("Tencent AI Lab — scBERT Team", "https://github.com/TencentAILabHealthcare/scBERT"),
    ],
    "atlas-consortia": [
        ("Human Cell Atlas (HCA)", "https://www.humancellatlas.org/"),
        ("BICCN (BRAIN Initiative Cell Census)", "https://biccn.org/"),
        ("HuBMAP", "https://hubmapconsortium.org/"),
        ("Human BioMolecular Atlas Program", "https://commonfund.nih.gov/hubmap"),
        ("Allen Brain Cell Atlas", "https://portal.brain-map.org/"),
        ("Fly Cell Atlas", "https://flycellatlas.org/"),
        ("Tabula Muris", "https://tabula-muris.ds.czbiohub.org/"),
        ("GTEx", "https://gtexportal.org/"),
    ],
}

for slug, items in resources_data.items():
    try:
        cat = ResourceCategory.objects.get(slug=slug)
    except ResourceCategory.DoesNotExist:
        continue
    for i, (title, url) in enumerate(items):
        obj, created = Resource.objects.get_or_create(
            category=cat, title=title,
            defaults={'url': url, 'sort_order': i}
        )
        status = "+" if created else "="
        print(f"    {status} [{slug}] {title}")

print(f"\nDone! Categories: {ResourceCategory.objects.count()}, Resources: {Resource.objects.count()}")
