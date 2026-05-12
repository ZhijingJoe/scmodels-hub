import threading
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import AnalysisJob
from .pipeline import run_analysis


def upload(request):
    if request.method == 'POST' and request.FILES.get('file'):
        f = request.FILES['file']
        if not f.name.endswith(('.h5ad', '.h5')):
            messages.error(request, 'Only .h5ad or .h5 files are supported.')
            return redirect('analysis_upload')

        job = AnalysisJob.objects.create(
            file=f,
            original_filename=f.name,
            min_genes=int(request.POST.get('min_genes', 200)),
            min_cells=int(request.POST.get('min_cells', 3)),
            n_top_genes=int(request.POST.get('n_top_genes', 2000)),
            resolution=float(request.POST.get('resolution', 0.8)),
        )

        # Run analysis in background thread
        t = threading.Thread(target=run_analysis, args=(job,), daemon=True)
        t.start()

        return redirect('analysis_result', job_id=job.id)

    jobs = AnalysisJob.objects.all()[:20]
    return render(request, 'analysis/upload.html', {'jobs': jobs})


def result(request, job_id):
    job = get_object_or_404(AnalysisJob, id=job_id)
    return render(request, 'analysis/result.html', {'job': job})
