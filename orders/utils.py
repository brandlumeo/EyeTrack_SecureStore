import logging
from io import BytesIO

from django.template.loader import get_template

logger = logging.getLogger(__name__)

try:
    from xhtml2pdf import pisa
except ModuleNotFoundError:
    pisa = None


def render_to_pdf(template_src, context_dict=None):
    """Render a template into a PDF byte stream when xhtml2pdf is available."""
    if pisa is None:
        logger.warning("xhtml2pdf is not installed. PDF generation is disabled.")
        return None

    template = get_template(template_src)
    html = template.render(context_dict or {})
    result = BytesIO()

    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if pdf.err:
        return None

    return result.getvalue()
