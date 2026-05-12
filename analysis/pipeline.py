"""FINAL v3 pipeline — handles raw OR preprocessed h5ad"""
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

        # Check if data is already processed (log-norm) or raw counts
        X_sample = adata.X[:10, :10]
        if hasattr(X_sample, 'toarray'): X_sample = X_sample.toarray()
        is_count = np.all(X_sample >= 0) and np.allclose(X_sample, X_sample.astype(int))
        has_raw = adata.raw is not None

        if not is_count and has_raw:
            # Restore raw counts from .raw
            adata = adata.raw.to_adata()
        elif not is_count:
            # Try to use raw counts
            pass  # We'll handle below

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

        # ── 3. Normalize (only if data is raw counts) ──
        adata.layers['counts'] = adata.X.copy()
        if is_count:
            sc.pp.normalize_total(adata, target_sum=1e4)
            sc.pp.log1p(adata)
            # Need HVG after normalization
            need_hvg = True
        else:
            # Already log-normed — skip normalization, but still need HVG
            need_hvg = True

        # ── 4. HVG ──
        if need_hvg:
            n_hvg = min(job.n_top_genes, adata.n_vars)
            try:
                sc.pp.highly_variable_genes(adata, n_top_genes=n_hvg, flavor='seurat_v3',
                                             layer='counts' if 'counts' in adata.layers else None)
            except:
                try:
                    sc.pp.highly_variable_genes(adata, n_top_genes=n_hvg, flavor='seurat')
                except:
                    adata.var['highly_variable'] = True
            if adata.var.highly_variable.sum() == 0:
                adata.var['highly_variable'] = True
            adata = adata[:, adata.var.highly_variable].copy()

        job.n_genes = adata.n_vars; job.save()

        # ── 5. Scale + cleanup ──
        sc.pp.scale(adata, max_value=10)
        if hasattr(adata.X, 'toarray'):
            X = adata.X.toarray()
        else:
            X = np.array(adata.X)
        if np.isnan(X).any() or np.isinf(X).any():
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            adata.X = X

        # ── 6. PCA ──
        n_comps = max(2, min(30, adata.n_vars - 1, adata.n_obs - 1))
        for solver in ['randomized', 'arpack', 'full']:
            try:
                sc.tl.pca(adata, svd_solver=solver, n_comps=n_comps)
                break
            except:
                if solver == 'full': raise

        # ── 7. Neighbors + UMAP + Leiden ──
        sc.pp.neighbors(adata, n_neighbors=min(job.n_neighbors, adata.n_obs-1), n_pcs=n_comps)
        sc.tl.umap(adata)
        sc.tl.leiden(adata, resolution=job.resolution)
        job.n_clusters = adata.obs['leiden'].nunique(); job.save()

        # UMAP plot
        fig, ax = plt.subplots(figsize=(9, 7))
        sc.pl.umap(adata, color='leiden', ax=ax, show=False, legend_loc='right margin', palette='tab20',
                   title=f"Leiden r={job.resolution} — {job.n_clusters} clusters")
        fig.tight_layout(); fig.savefig(out_dir / 'umap.png', dpi=120, bbox_inches='tight'); plt.close(fig)

        # ── 8. Markers ──
        sc.tl.rank_genes_groups(adata, 'leiden', method='wilcoxon', n_genes=job.n_markers)
        rgg = adata.uns['rank_genes_groups']
        clusters = sorted(adata.obs['leiden'].cat.categories, key=lambda x: int(x))

        marker_rows = []
        for cl in clusters[:10]:
            for rank in range(min(job.n_markers, len(rgg['names'][cl]))):
                marker_rows.append({
                    'cluster': cl, 'rank': rank+1, 'gene': rgg['names'][cl][rank],
                    'logfoldchanges': rgg['logfoldchanges'][cl][rank],
                    'pvals': rgg['pvals'][cl][rank],
                    'pvals_adj': rgg['pvals_adj'][cl][rank],
                })
        pd.DataFrame(marker_rows).to_csv(out_dir / 'markers.csv', index=False)
        top_genes = list({r['gene'] for r in marker_rows})[:25]

        # ── 9-11. Plots ──
        if top_genes:
            fig, ax = plt.subplots(figsize=(max(10, len(top_genes)*0.35), 5))
            sc.pl.dotplot(adata, top_genes, groupby='leiden', ax=ax, show=False, standard_scale='var')
            fig.tight_layout(); fig.savefig(out_dir / 'dotplot.png', dpi=120, bbox_inches='tight'); plt.close(fig)

            top6 = top_genes[:6]
            fig, ax = plt.subplots(figsize=(max(8, len(top6)*1.8), 4))
            sc.pl.stacked_violin(adata, top6, groupby='leiden', ax=ax, show=False, rotation=45)
            fig.tight_layout(); fig.savefig(out_dir / 'vlnplot.png', dpi=120, bbox_inches='tight'); plt.close(fig)

            fig, ax = plt.subplots(figsize=(max(8, len(top6)*0.6), max(5, job.n_clusters*0.3)))
            sc.pl.heatmap(adata, top6, groupby='leiden', ax=ax, show=False, cmap='RdBu_r', standard_scale='var')
            fig.tight_layout(); fig.savefig(out_dir / 'heatmap.png', dpi=120, bbox_inches='tight'); plt.close(fig)

        # ── 12. Volcano ──
        if len(clusters) > 1 and '0' in clusters:
            sc.tl.rank_genes_groups(adata, 'leiden', groups=['0'], reference='rest', method='wilcoxon', n_genes=50)
            rgg2 = adata.uns['rank_genes_groups']
            de = pd.DataFrame({
                'gene': rgg2['names']['0'], 'logfoldchanges': rgg2['logfoldchanges']['0'],
                'pvals': rgg2['pvals']['0'], 'pvals_adj': rgg2['pvals_adj']['0'],
            })
            de['-log10(pval)'] = -np.log10(de['pvals'].clip(1e-300))
            de['significant'] = (de['pvals_adj'] < 0.05) & (abs(de['logfoldchanges']) > 1)

            fig, ax = plt.subplots(figsize=(10, 7))
            colors = {True: '#c44e52', False: '#aaaaaa'}
            ax.scatter(de['logfoldchanges'], de['-log10(pval)'],
                       c=[colors[s] for s in de['significant']], alpha=0.5, s=12, edgecolors='none')
            for _, row in de[de['significant']].nlargest(10, 'logfoldchanges').iterrows():
                ax.annotate(row['gene'], (row['logfoldchanges'], row['-log10(pval)']),
                            fontsize=7, alpha=0.8, xytext=(5,5), textcoords='offset points')
            ax.axhline(-np.log10(0.05), color='grey', linestyle='--', alpha=0.5)
            ax.set_xlabel('log2 FC'); ax.set_ylabel('-log10(p)'); ax.set_title('Cluster 0 vs Rest')
            sns.despine(ax=ax)
            fig.tight_layout(); fig.savefig(out_dir / 'volcano.png', dpi=120, bbox_inches='tight'); plt.close(fig)

        job.status = 'completed'; job.save()

    except Exception:
        job.status = 'failed'
        job.error_message = traceback.format_exc()[-2000:]
        job.save()
