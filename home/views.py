import os

from django.conf import settings
from django.http import Http404, HttpResponse

def serve_spa(request, path=""):
    """Serve Vue SPA index.html for all non-API routes (used by root and catch-all in urls.py)."""
    index_path = os.path.join(settings.BASE_DIR, "www", "index.html")
    if not os.path.exists(index_path):
        raise Http404("SPA index.html not found")
    with open(index_path, "rb") as f:
        content = f.read()
    return HttpResponse(content, content_type="text/html")