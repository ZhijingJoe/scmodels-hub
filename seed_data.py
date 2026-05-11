import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from scmodels_app.models import ModelEntry, Tag

# Create tags
tag_names_list = [
    "Transformer", "Gene Expression", "scRNA-seq", "Foundation Model",
    "Cell Atlas", "GPT", "Masked Modeling", "Multi-omics", "Spatial",
    "Perturbation", "Generative", "Virtual Cell", "Geneformer",
    "scGPT", "scFoundation", "scBERT", "Cross-species"
]
tags = {}
for name in tag_names_list:
    tags[name], _ = Tag.objects.get_or_create(name=name)

entries = [
    {
        "name": "scGPT",
        "short_description": "Generative pre-trained transformer for single-cell biology. Pre-trained on 33M+ cells from CELLxGENE.",
        "description": "scGPT is a foundation model for single-cell biology built upon a generative pre-trained transformer architecture. It is trained on over 33 million human cells from the CELLxGENE database and can be fine-tuned for various downstream tasks including cell type annotation, gene perturbation prediction, multi-omics integration, and batch correction.",
        "paper_title": "scGPT: Toward Building a Foundation Model for Single-Cell Multi-Omics Using Generative AI",
        "paper_url": "https://www.nature.com/articles/s41592-024-02201-0",
        "paper_doi": "10.1038/s41592-024-02201-0",
        "authors": "Cui H, Wang C, Maan H, Pang K, Luo F, Duan N, Wang B",
        "publication_date": "2024-02-26",
        "journal": "Nature Methods",
        "github_url": "https://github.com/bowang-lab/scGPT",
        "model_type": "foundation",
        "modality": "scrna",
        "architecture": "Transformer (GPT-style)",
        "pretraining_data": "CELLxGENE (33M cells)",
        "parameter_count": "~300M",
        "featured": True,
        "entry_tags": ["scGPT", "Foundation Model", "Transformer", "Gene Expression"]
    },
    {
        "name": "Geneformer",
        "short_description": "Context-aware foundation model for gene network predictions. Transfer learning from 30M single-cell transcriptomes.",
        "description": "Geneformer is a context-aware, attention-based model pre-trained on a large-scale corpus of ~30M human single-cell transcriptomes. It uses a Transformer encoder architecture with masked language modeling to learn gene network dynamics in a self-supervised fashion.",
        "paper_title": "Transfer learning enables predictions in network biology",
        "paper_url": "https://www.nature.com/articles/s41586-023-06139-9",
        "paper_doi": "10.1038/s41586-023-06139-9",
        "authors": "Theodoris CV, Xiao L, Chopra A, Chaffin MD, Al Sayed ZR, Hill MC, Mantineo H, Brydon EM, Zeng Z, Liu XS, Ellinor PT",
        "publication_date": "2023-05-31",
        "journal": "Nature",
        "github_url": "https://github.com/ctheodoris/Geneformer",
        "huggingface_url": "https://huggingface.co/ctheodoris/Geneformer",
        "model_type": "geneformer",
        "modality": "scrna",
        "architecture": "Transformer Encoder (BERT-style)",
        "pretraining_data": "Genecorpus-30M (30M cells)",
        "parameter_count": "~100M",
        "embedding_dim": 256,
        "context_length": 2048,
        "featured": True,
        "entry_tags": ["Geneformer", "Masked Modeling", "Gene Expression", "Foundation Model"]
    },
    {
        "name": "scFoundation",
        "short_description": "Large-scale pre-trained model for single-cell transcriptomics with 100M parameters, trained on 50M+ cells.",
        "description": "scFoundation is a large-scale foundation model for single-cell transcriptomics with 100 million parameters, pre-trained on over 50 million human cells. It features a novel xTrimoFormer architecture designed to handle the extreme sparsity and high dimensionality of scRNA-seq data.",
        "paper_title": "Large-scale foundation model on single-cell transcriptomics",
        "paper_url": "https://www.nature.com/articles/s41592-024-02305-7",
        "paper_doi": "10.1038/s41592-024-02305-7",
        "authors": "Hao M, Gong J, Zeng X, Liu C, Guo Y, Cheng X, Wang T, Ma J, Zhang X, Song L",
        "publication_date": "2024-06-06",
        "journal": "Nature Methods",
        "github_url": "https://github.com/biomap-research/scFoundation",
        "model_type": "foundation",
        "modality": "scrna",
        "architecture": "xTrimoFormer (asymmetric encoder-decoder)",
        "pretraining_data": "50M+ human cells",
        "parameter_count": "100M",
        "embedding_dim": 512,
        "featured": True,
        "entry_tags": ["scFoundation", "Foundation Model", "Gene Expression"]
    },
    {
        "name": "UCE",
        "short_description": "Universal Cell Embedding — species-agnostic cell representation model for cross-species analysis.",
        "description": "The Universal Cell Embedding (UCE) model produces a unified embedding space for cells across species. It is trained using a protein language model (ESM) to map gene expression profiles to a shared latent space, enabling cross-species cell type comparisons.",
        "paper_title": "Universal cell embeddings for cross-species single-cell analysis",
        "paper_url": "https://www.biorxiv.org/content/10.1101/2023.11.28.568918",
        "authors": "Rosen Y, Brbic M, Roohani Y, Swanson K, Li Z, Leskovec J",
        "publication_date": "2023-11-28",
        "journal": "bioRxiv",
        "github_url": "https://github.com/snap-stanford/UCE",
        "model_type": "foundation",
        "modality": "scrna",
        "architecture": "Protein language model + gene expression encoder",
        "pretraining_data": "CELLxGENE + cross-species scRNA-seq",
        "entry_tags": ["Foundation Model", "Cross-species", "Gene Expression", "scRNA-seq"]
    },
    {
        "name": "scBERT",
        "short_description": "BERT-based pre-trained model for single-cell transcriptomics with gene-level tokenization.",
        "description": "scBERT adapts the BERT architecture for single-cell transcriptomics by treating each gene as a token. It is pre-trained on large-scale scRNA-seq data using masked gene expression prediction and achieves strong performance on cell type annotation tasks.",
        "paper_title": "scBERT as a large-scale pretrained deep language model for cell type annotation of single-cell RNA-seq data",
        "paper_url": "https://www.nature.com/articles/s42256-022-00534-z",
        "paper_doi": "10.1038/s42256-022-00534-z",
        "authors": "Yang F, Wang W, Wang F, Fang Y, Tang D, Huang J, Lu H, Yao J",
        "publication_date": "2022-09-26",
        "journal": "Nature Machine Intelligence",
        "github_url": "https://github.com/TencentAILabHealthcare/scBERT",
        "model_type": "foundation",
        "modality": "scrna",
        "architecture": "Transformer Encoder (BERT-style)",
        "pretraining_data": "PanglaoDB (1M+ cells)",
        "parameter_count": "~100M",
        "entry_tags": ["scBERT", "Masked Modeling", "Gene Expression"]
    },
    {
        "name": "CELLxGENE Census Models",
        "short_description": "Foundation models from CZI, trained on CELLxGENE Census data (50M+ cells).",
        "description": "CZI's CELLxGENE Census project provides pre-trained embedding models and a unified data platform for single-cell transcriptomics. Models include PCA, scVI, and geneformer-style embeddings pre-computed on the full CELLxGENE corpus.",
        "paper_title": "CELLxGENE Census: a unified platform for single-cell data",
        "paper_url": "https://www.biorxiv.org/content/10.1101/2023.07.27.550749",
        "authors": "CZI Single-Cell Biology Program",
        "publication_date": "2023-07-27",
        "journal": "bioRxiv",
        "github_url": "https://github.com/chanzuckerberg/cellxgene-census",
        "website_url": "https://cellxgene.cziscience.com/",
        "model_type": "foundation",
        "modality": "scrna",
        "pretraining_data": "CELLxGENE (50M+ cells)",
        "entry_tags": ["Cell Atlas", "Foundation Model", "Gene Expression", "scRNA-seq"]
    },
    {
        "name": "SATURN",
        "short_description": "Cross-species single-cell foundation model using protein language models.",
        "description": "SATURN combines scRNA-seq data with protein language models (ProtT5) to create species-agnostic cell embeddings. It maps genes to protein embeddings via orthology, enabling cross-species cell type annotation without shared gene symbols.",
        "paper_title": "Cross-species single-cell foundation model using protein language models",
        "paper_url": "https://www.nature.com/articles/s41586-023-06703-0",
        "authors": "Rosen Y, Brbic M, Swanson K, Roohani Y, Leskovec J",
        "publication_date": "2023-11-01",
        "journal": "Nature",
        "github_url": "https://github.com/snap-stanford/SATURN",
        "model_type": "foundation",
        "modality": "scrna",
        "architecture": "Protein language model (ProtT5) + autoencoder",
        "pretraining_data": "Tabula Sapiens + cross-species scRNA-seq",
        "entry_tags": ["Cross-species", "Foundation Model", "Gene Expression"]
    },
    {
        "name": "Virtual Cell Models",
        "short_description": "Generative models for simulating single-cell responses to perturbations.",
        "description": "The Virtual Cell initiative aims to build generative models that can simulate cellular responses to genetic and chemical perturbations. By learning from large-scale perturb-seq data, these models predict how individual cells change their gene expression programs in response to interventions.",
        "paper_title": "Building virtual cells with generative AI",
        "paper_url": "https://www.biorxiv.org/content/10.1101/2024.01.01.573790",
        "authors": "Bunne C, Roohani Y, Krause A, Leskovec J",
        "publication_date": "2024-01-01",
        "journal": "bioRxiv",
        "model_type": "virtual_cell",
        "modality": "scrna",
        "architecture": "Conditional generative model",
        "pretraining_data": "Perturb-seq datasets",
        "entry_tags": ["Virtual Cell", "Perturbation", "Generative"]
    },
]

for e in entries:
    tag_names = e.pop("entry_tags", [])
    obj, created = ModelEntry.objects.get_or_create(name=e["name"], defaults=e)
    if created:
        for tn in tag_names:
            obj.tags.add(tags[tn])
        print("  +", e["name"])
    else:
        print("  =", e["name"], "(exists)")

print(f"Done! Total entries: {ModelEntry.objects.count()}")
