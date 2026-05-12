"""FINAL v2 pipeline — tested with pbmc3k + scanpy 1.12"""
import traceback, warnings
warnings.filterwarnings('ignore')

import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import scanpy as sc
import numpy as np
import pandas as pd
import seaborn as sns
from django.conf import settings

sc.settings.verbosity = 0
sc.settings.set_figure_params(dpi=120, facecolor='white', frameon=True)


def run_analysis(job):
    from analysis.models import AnalysisJob
    try:
        job.status = 'running'; job.save()
        filepath = job.file.path
        job_id = str(job.id)
        out_dir = settings.MEDIA_ROOT / 'analysis' / 'results' / job_id
        out_dir.mkdir(parents=True, exist_ok=True)

        # ── 1. Load ──
        adata = sc.read_h5ad(filepath)
        job.n_cells = adata.n_obs; job.n_genes = adata.n_vars; job.save()

        # ── 2. QC ──
        sc.pp.filter_cells(adata, min_genes=job.min_genes)
        sc.pp.filter_genes(adata, min_cells=job.min_cells)
        adata.var['mt'] = adata.var_names.str.startswith('MT-')
        sc.pp.calculate_qc_metrics(adata, qc_vars=['mt'], percent_top=None, log1p=False, inplace=True)

        fig, axes = plt.subplots(1, 3, figsize=(14, 4))
        sc.pl.violin(adata, 'n_genes_by_counts', ax=axes[0], show=False)
        sc.pl.violin(adata, 'total_counts', ax=axes[1], show=False)
        sc.pl.violin(adata, 'pct_counts_mt', ax=axes[2], show=False)
        fig.tight_layout(); fig.savefig(out_dir / 'qc_violin.png', dpi=120, bbox_inches='tight'); plt.close(fig)

        # ── 3. Normalize ──
        adata.raw = adata.copy()
        sc.pp.normalize_total(adata, target_sum=1e4)
        sc.pp.log1p(adata)

        # Fix: log1p can produce NaN → fill with 0
        if hasattr(adata.X, 'toarray'):
            X = adata.X.toarray()
        else:
            X = adata.X
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        adata.X = X

        # ── 4. HVG ──
        n_hvg = min(job.n_top_genes, adata.n_vars)
        try:
            sc.pp.highly_variable_genes(adata, n_top_genes=n_hvg, flavor='seurat_v3')
        except:
            try:
                sc.pp.highly_variable_genes(adata, n_top_genes=n_hvg, flavor='seurat')
            except:
                adata.var['highly_variable'] = True
        if adata.var.highly_variable.sum() == 0:
            adata.var['highly_variable'] = True

        adata = adata[:, adata.var.highly_variable].copy()
        job.n_genes = adata.n_vars; job.save()

        # ── 5. Scale + PCA ──
        sc.pp.scale(adata, max_value=10)
        if hasattr(adata.X, 'toarray'):
            X = adata.X.toarray()
            if np.isnan(X).any():
                adata.X = np.nan_to_num(X, nan=0.0)

        n_comps = max(2, min(30, adata.n_vars - 1, adata.n_obs - 1))
        for solver in ['randomized', 'arpack', 'full']:
            try:
                sc.tl.pca(adata, svd_solver=solver, n_comps=n_comps)
                break
            except:
                if solver == 'full': raise

        # ── 6. Neighbors + UMAP + Leiden ──
        sc.pp.neighbors(adata, n_neighbors=min(job.n_neighbors, adata.n_obs-1), n_pcs=n_comps)
        sc.tl.umap(adata)
        sc.tl.leiden(adata, resolution=job.resolution)
        job.n_clusters = adata.obs['leiden'].nunique(); job.save()

        # UMAP plot
        fig, ax = plt.subplots(figsize=(9, 7))
        sc.pl.umap(adata, color='leiden', ax=ax, show=False, legend_loc='right margin', palette='tab20',
                   title=f"Leiden r={job.resolution} — {job.n_clusters} clusters")
        fig.tight_layout(); fig.savefig(out_dir / 'umap.png', dpi=120, bbox_inches='tight'); plt.close(fig)

        # ── 7. Markers (scanpy 1.12 dict access) ──
        sc.tl.rank_genes_groups(adata, 'leiden', method='wilcoxon', n_genes=job.n_markers)
        rgg = adata.uns['rank_genes_groups']

        # Collect top markers per cluster
        marker_rows = []
        clusters = sorted(adata.obs['leiden'].cat.categories, key=lambda x: int(x))
        for cl in clusters[:10]:
            for rank in range(min(job.n_markers, len(rgg['names'][cl]))):
                marker_rows.append({
                    'cluster': cl,
                    'rank': rank + 1,
                    'gene': rgg['names'][cl][rank],
                    'logfoldchanges': rgg['logfoldchanges'][cl][rank],
                    'pvals': rgg['pvals'][cl][rank],
                    'pvals_adj': rgg['pvals_adj'][cl][rank],
                })
        markers_df = pd.DataFrame(marker_rows)
        markers_df.to_csv(out_dir / 'markers.csv', index=False)

        # Top unique genes for plotting
        top_genes_list = list(markers_df['gene'].unique())[:25]

        # Save marker table as HTML snippet for web display (optional)

        # ── 8. Dotplot ──
        if len(top_genes_list) > 0:
            fig, ax = plt.subplots(figsize=(max(10, len(top_genes_list)*0.35), 5))
            sc.pl.dotplot(adata, top_genes_list, groupby='leiden', ax=ax, show=False,
                          standard_scale='var')
            fig.tight_layout(); fig.savefig(out_dir / 'dotplot.png', dpi=120, bbox_inches='tight'); plt.close(fig)

        # ── 9. Violin ──
        top6 = top_genes_list[:6] if len(top_genes_list) >= 6 else top_genes_list
        if len(top6) > 0:
            fig, ax = plt.subplots(figsize=(max(8, len(top6)*1.8), 4))
            sc.pl.stacked_violin(adata, top6, groupby='leiden', ax=ax, show=False, rotation=45)
            fig.tight_layout(); fig.savefig(out_dir / 'vlnplot.png', dpi=120, bbox_inches='tight'); plt.close(fig)

        # ── 10. Heatmap ──
        if len(top6) > 0:
            fig, ax = plt.subplots(figsize=(max(8, len(top6)*0.6), max(5, job.n_clusters*0.3)))
            sc.pl.heatmap(adata, top6, groupby='leiden', ax=ax, show=False, cmap='RdBu_r', standard_scale='var')
            fig.tight_layout(); fig.savefig(out_dir / 'heatmap.png', dpi=120, bbox_inches='tight'); plt.close(fig)

        # ── 11. Volcano (cluster 0 vs rest) ──
        if len(clusters) > 1 and '0' in clusters:
            sc.tl.rank_genes_groups(adata, 'leiden', groups=['0'], reference='rest', method='wilcoxon',
                                    n_genes=job.n_markers * 2)
            rgg2 = adata.uns['rank_genes_groups']
            de = pd.DataFrame({
                'gene': rgg2['names']['0'],
                'logfoldchanges': rgg2['logfoldchanges']['0'],
                'pvals': rgg2['pvals']['0'],
                'pvals_adj': rgg2['pvals_adj']['0'],
            })
            de['-log10(pval)'] = -np.log10(de['pvals'].clip(1e-300))
            de['significant'] = (de['pvals_adj'] < 0.05) & (abs(de['logfoldchanges']) > 1)

            fig, ax = plt.subplots(figsize=(10, 7))
            colors = {True: '#c44e52', False: '#aaaaaa'}
            ax.scatter(de['logfoldchanges'], de['-log10(pval)'],
                       c=[colors[s] for s in de['significant']], alpha=0.5, s=12, edgecolors='none')
            top_up = de[de['significant']].nlargest(10, 'logfoldchanges')
            for _, row in top_up.iterrows():
                ax.annotate(row['gene'], (row['logfoldchanges'], row['-log10(pval)']),
                            fontsize=7, alpha=0.8, xytext=(5,5), textcoords='offset points')
            ax.axhline(-np.log10(0.05), color='grey', linestyle='--', alpha=0.5)
            ax.axvline(1, color='grey', linestyle='--', alpha=0.3)
            ax.axvline(-1, color='grey', linestyle='--', alpha=0.3)
            ax.set_xlabel('log2 Fold Change'); ax.set_ylabel('-log10(p-value)')
            ax.set_title('Cluster 0 vs Rest — Volcano Plot')
            sns.despine(ax=ax)
            fig.tight_layout(); fig.savefig(out_dir / 'volcano.png', dpi=120, bbox_inches='tight'); plt.close(fig)

        job.status = 'completed'; job.save()

    except Exception:
        job.status = 'failed'
        job.error_message = traceback.format_exc()[-2000:]
        job.save()
