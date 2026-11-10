"""Serve page videos with HTTP Range support.

WhiteNoise answers Range requests with a sliced file object, which the
LiteSpeed/Passenger WSGI file wrapper on the live host cannot send
("io.UnsupportedOperation: fileno"), so video requests failed with 500.
Browsers (Safari in particular) need 206 Partial Content to play video,
so this view reads the requested bytes itself and returns them.
"""
import os
import re

from django.contrib.staticfiles import finders
from django.http import Http404, HttpResponse

# Only these files under static/video/ can be served by this view.
ALLOWED_VIDEOS = {"services-hero.mp4"}
RANGE_RE = re.compile(r"^bytes=(\d*)-(\d*)$")


def static_video(request, name):
    if name not in ALLOWED_VIDEOS:
        raise Http404
    path = finders.find(f"video/{name}")
    if not path or not os.path.isfile(path):
        raise Http404

    size = os.path.getsize(path)
    start, end = 0, size - 1
    match = RANGE_RE.match(request.headers.get("Range", "").strip())
    partial = False
    if match and (match.group(1) or match.group(2)):
        if match.group(1):
            start = int(match.group(1))
            end = int(match.group(2)) if match.group(2) else size - 1
        else:  # suffix range: last N bytes
            start = max(size - int(match.group(2)), 0)
        end = min(end, size - 1)
        if start > end or start >= size:
            response = HttpResponse(status=416)
            response["Content-Range"] = f"bytes */{size}"
            return response
        partial = True

    with open(path, "rb") as handle:
        handle.seek(start)
        data = handle.read(end - start + 1)

    response = HttpResponse(data, status=206 if partial else 200, content_type="video/mp4")
    response["Accept-Ranges"] = "bytes"
    response["Content-Length"] = str(len(data))
    if partial:
        response["Content-Range"] = f"bytes {start}-{end}/{size}"
    return response
