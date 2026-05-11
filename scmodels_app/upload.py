import os
import uuid
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings


@csrf_exempt
def upload_image(request):
    """Handle image upload from Markdown editor. Returns markdown image syntax."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    f = request.FILES.get('image')
    if not f:
        return JsonResponse({'error': 'No image'}, status=400)

    # Validate
    ext = os.path.splitext(f.name)[1].lower()
    if ext not in ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'):
        return JsonResponse({'error': f'Unsupported format: {ext}'}, status=400)
    if f.size > 20 * 1024 * 1024:
        return JsonResponse({'error': 'Max 20MB'}, status=400)

    # Save to media/uploads/YYYY/MM/
    date_path = datetime.now().strftime('%Y/%m')
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', date_path)
    os.makedirs(upload_dir, exist_ok=True)

    filename = f"{uuid.uuid4().hex[:8]}_{f.name}"
    filepath = os.path.join(upload_dir, filename)
    with open(filepath, 'wb+') as dest:
        for chunk in f.chunks():
            dest.write(chunk)

    url = f"{settings.MEDIA_URL}uploads/{date_path}/{filename}"
    return JsonResponse({
        'success': 1,
        'url': url,
        'message': '![image](' + url + ')'
    })
