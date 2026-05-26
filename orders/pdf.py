from decimal import Decimal


PAGE_WIDTH = 595.0
PAGE_HEIGHT = 842.0
PAGE_MARGIN = 42.0
CONTENT_WIDTH = PAGE_WIDTH - (PAGE_MARGIN * 2)


def _escape_pdf_text(value):
    text = str(value or "").encode("latin-1", "replace").decode("latin-1")
    return (
        text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def _rgb(color):
    return tuple(channel / 255 for channel in color)
    


def _format_currency(value):
    amount = Decimal(value or "0.00").quantize(Decimal("0.01"))
    return f"INR {amount:,.2f}"


def _estimate_text_width(text, size, bold=False):
    factor = 0.60 if bold else 0.56
    normalized = str(text or "").encode("latin-1", "replace").decode("latin-1")
    return len(normalized) * size * factor


def _split_long_word(word, max_width, font_size, bold=False):
    if _estimate_text_width(word, font_size, bold=bold) <= max_width:
        return [word]

    chunks = []
    current = ""
    for character in str(word or ""):
        candidate = f"{current}{character}"
        if current and _estimate_text_width(candidate, font_size, bold=bold) > max_width:
            chunks.append(current)
            current = character
        else:
            current = candidate

    if current:
        chunks.append(current)
    return chunks or [word]


def _wrap_text(text, max_width, font_size, bold=False):
    raw_words = str(text or "").split()
    if not raw_words:
        return [""]

    words = []
    for word in raw_words:
        words.extend(_split_long_word(word, max_width, font_size, bold=bold))

    lines = []
    current = ""

    for word in words:
        candidate = word if not current else f"{current} {word}"
        if not current or _estimate_text_width(candidate, font_size, bold=bold) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class _PdfDocument:
    def __init__(self):
        self.pages = []

    def new_page(self):
        page = []
        self.pages.append(page)
        return page

    def add(self, page, command):
        page.append(command)

    def set_fill(self, page, color):
        r, g, b = _rgb(color)
        self.add(page, f"{r:.4f} {g:.4f} {b:.4f} rg")

    def set_stroke(self, page, color):
        r, g, b = _rgb(color)
        self.add(page, f"{r:.4f} {g:.4f} {b:.4f} RG")

    def set_line_width(self, page, width):
        self.add(page, f"{width:.2f} w")

    def rect(self, page, x, y, width, height, fill=False, stroke=True):
        operator = "B" if fill and stroke else "f" if fill else "S"
        self.add(page, f"{x:.2f} {y:.2f} {width:.2f} {height:.2f} re {operator}")

    def line(self, page, x1, y1, x2, y2):
        self.add(page, f"{x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S")

    def text(self, page, x, y, text, size=12, font="F1", color=(17, 24, 39)):
        if text is None:
            return
        self.set_fill(page, color)
        escaped = _escape_pdf_text(text)
        self.add(page, f"BT /{font} {size:.2f} Tf 1 0 0 1 {x:.2f} {y:.2f} Tm ({escaped}) Tj ET")

    def render(self):
        objects = []

        def add_object(payload):
            objects.append(payload)
            return len(objects)

        catalog_id = add_object("<< /Type /Catalog /Pages 2 0 R >>")
        pages_id = add_object("")
        font_regular_id = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        font_bold_id = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

        page_ids = []
        for page_commands in self.pages:
            content_stream = "\n".join(page_commands).encode("latin-1")
            content_id = add_object(
                f"<< /Length {len(content_stream)} >>\nstream\n{content_stream.decode('latin-1')}\nendstream"
            )
            page_id = add_object(
                "<< /Type /Page /Parent 2 0 R "
                f"/MediaBox [0 0 {PAGE_WIDTH:.2f} {PAGE_HEIGHT:.2f}] "
                f"/Resources << /Font << /F1 {font_regular_id} 0 R /F2 {font_bold_id} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            )
            page_ids.append(page_id)

        kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
        objects[pages_id - 1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>"

        lines = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
        offsets = [0]
        for index, payload in enumerate(objects, start=1):
            offsets.append(sum(len(chunk) for chunk in lines))
            lines.append(f"{index} 0 obj\n{payload}\nendobj\n".encode("latin-1"))

        xref_offset = sum(len(chunk) for chunk in lines)
        lines.append(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
        lines.append(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            lines.append(f"{offset:010d} 00000 n \n".encode("latin-1"))
        lines.append(
            (
                f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
                f"startxref\n{xref_offset}\n%%EOF"
            ).encode("latin-1")
        )
        return b"".join(lines)


def build_invoice_pdf(invoice, order, items, latest_payment, invoice_display):
    document = _PdfDocument()
    current_page = None
    page_number = 0

    navy = (11, 27, 55)
    gold = (245, 166, 35)
    gold_soft = (255, 248, 233)
    border = (217, 223, 232)
    text = (20, 27, 44)
    muted = (95, 108, 129)
    card = (246, 248, 252)
    green = (27, 126, 88)

    def to_pdf_y(top, height=0):
        return PAGE_HEIGHT - top - height

    def rect_top(x, top, width, height, fill_color=None, stroke_color=None, line_width=1):
        if fill_color:
            document.set_fill(current_page, fill_color)
        if stroke_color:
            document.set_stroke(current_page, stroke_color)
        document.set_line_width(current_page, line_width)
        document.rect(current_page, x, to_pdf_y(top, height), width, height, fill=bool(fill_color), stroke=bool(stroke_color))

    def line_top(x1, top1, x2, top2, stroke_color=border, line_width=1):
        document.set_stroke(current_page, stroke_color)
        document.set_line_width(current_page, line_width)
        document.line(current_page, x1, to_pdf_y(top1), x2, to_pdf_y(top2))

    def text_top(x, top, value, size=12, font="F1", color=text):
        document.text(current_page, x, PAGE_HEIGHT - top - size, value, size=size, font=font, color=color)

    def text_right(right_edge, top, value, size=12, font="F1", color=text):
        width = _estimate_text_width(value, size, bold=(font == "F2"))
        text_top(right_edge - width, top, value, size=size, font=font, color=color)

    def text_block(x, top, value, width, size=12, font="F1", color=text, line_height=1.45):
        lines = _wrap_text(value, width, size, bold=(font == "F2"))
        cursor = top
        step = size * line_height
        for line in lines:
            text_top(x, cursor, line, size=size, font=font, color=color)
            cursor += step
        return cursor

    def block_height(value, width, size=12, font="F1", line_height=1.45):
        lines = _wrap_text(value, width, size, bold=(font == "F2"))
        return max(1, len(lines)) * size * line_height

    def add_footer():
        line_top(PAGE_MARGIN, PAGE_HEIGHT - 78, PAGE_WIDTH - PAGE_MARGIN, PAGE_HEIGHT - 78, stroke_color=border)
        text_top(PAGE_MARGIN, PAGE_HEIGHT - 68, f"Invoice {invoice.invoice_number}", size=9, font="F2", color=muted)
        text_top(PAGE_WIDTH - PAGE_MARGIN - 155, PAGE_HEIGHT - 68, f"Page {page_number}", size=9, color=muted)

    def start_page(include_intro):
        nonlocal current_page, page_number
        current_page = document.new_page()
        page_number += 1
        if include_intro:
            rect_top(PAGE_MARGIN, 36, CONTENT_WIDTH, 112, fill_color=navy)
            rect_top(PAGE_MARGIN, 36, CONTENT_WIDTH, 6, fill_color=gold)
            text_top(PAGE_MARGIN + 22, 64, "EYETRACK SOLUTIONS", size=19, font="F2", color=(255, 255, 255))
            text_top(PAGE_MARGIN + 22, 92, "Tax Invoice", size=12, font="F2", color=(255, 237, 196))
            text_top(
                PAGE_MARGIN + 22,
                116,
                "Payyoli-Perambra Rd, Kozhikode, Kerala 673522 | info@etsgrp.in | +91 7994357565",
                size=10,
                color=(224, 232, 243),
            )
            text_top(PAGE_WIDTH - PAGE_MARGIN - 156, 66, invoice.invoice_number, size=16, font="F2", color=(255, 255, 255))
            text_top(PAGE_WIDTH - PAGE_MARGIN - 156, 96, f"Issued {invoice.created_at:%b %d, %Y}", size=10, color=(224, 232, 243))
        else:
            text_top(PAGE_MARGIN, 48, f"Invoice {invoice.invoice_number}", size=16, font="F2", color=navy)
            line_top(PAGE_MARGIN, 74, PAGE_WIDTH - PAGE_MARGIN, 74, stroke_color=border)
        add_footer()

    start_page(include_intro=True)

    card_top = 174
    card_width = (CONTENT_WIDTH - 24) / 4
    summary_cards = [
        ("Order", f"#{order.id}"),
        ("Order Date", order.created_at.strftime("%b %d, %Y")),
        ("Payment", invoice_display["payment_status"]),
        ("Amount", _format_currency(invoice.total_amount)),
    ]
    for index, (label, value) in enumerate(summary_cards):
        x = PAGE_MARGIN + (index * (card_width + 8))
        rect_top(x, card_top, card_width, 72, fill_color=card, stroke_color=border)
        text_top(x + 14, card_top + 16, label.upper(), size=9, font="F2", color=muted)
        text_top(x + 14, card_top + 38, value, size=13, font="F2", color=text)

    section_top = 270
    left_width = 254
    right_width = CONTENT_WIDTH - left_width - 18
    left_x = PAGE_MARGIN
    right_x = PAGE_MARGIN + left_width + 18

    address_width = left_width - 36
    address_height = block_height(invoice_display["address"], address_width, size=10.5, line_height=1.45)
    left_height = max(148, 110 + address_height)

    details_x = right_x + 20
    details_label_width = 92
    details_value_x = details_x + details_label_width + 8
    details_value_width = right_width - (details_value_x - right_x) - 20
    detail_rows = [
        ("Invoice Number", invoice.invoice_number),
        ("Order Reference", f"ET-{order.id:06d}"),
        ("Payment Method", invoice_display["payment_method"]),
        ("Transaction Ref", invoice_display["transaction_id"]),
    ]
    detail_specs = []
    right_height = 56
    for label, value in detail_rows:
        value_height = block_height(value, details_value_width, size=10.5, line_height=1.32)
        row_height = max(16, value_height)
        detail_specs.append((label, value, row_height))
        right_height += row_height + 16
    right_height = max(148, right_height)
    section_height = max(left_height, right_height)

    rect_top(left_x, section_top, left_width, section_height, fill_color=gold_soft, stroke_color=border)
    rect_top(right_x, section_top, right_width, section_height, fill_color=card, stroke_color=border)

    text_top(left_x + 18, section_top + 18, "Billed To", size=10, font="F2", color=muted)
    text_top(left_x + 18, section_top + 40, invoice_display["recipient_name"], size=14, font="F2", color=text)
    next_top = text_block(left_x + 18, section_top + 64, invoice_display["address"], left_width - 36, size=10.5, color=muted)
    text_top(left_x + 18, next_top + 10, order.email, size=10, color=muted)
    text_top(left_x + 18, next_top + 28, order.phone, size=10, color=muted)

    text_top(details_x, section_top + 18, "Invoice Details", size=10, font="F2", color=muted)
    top_cursor = section_top + 42
    divider_right = right_x + right_width - 20
    for index, (label, value, row_height) in enumerate(detail_specs):
        text_top(details_x, top_cursor + 2, label, size=9.5, font="F2", color=muted)
        text_block(
            details_value_x,
            top_cursor,
            value,
            details_value_width,
            size=10.5,
            font="F2" if label == "Invoice Number" else "F1",
            color=text,
            line_height=1.32,
        )
        if index != len(detail_specs) - 1:
            divider_top = top_cursor + row_height + 8
            line_top(details_x, divider_top, divider_right, divider_top, stroke_color=border)
        top_cursor += row_height + 16

    current_top = section_top + section_height
    if order.order_notes:
        notes_top = current_top + 18
        notes_height = max(82, 46 + block_height(order.order_notes, CONTENT_WIDTH - 32, size=9.5, line_height=1.35))
        rect_top(PAGE_MARGIN, notes_top, CONTENT_WIDTH, notes_height, fill_color=gold_soft, stroke_color=border)
        text_top(PAGE_MARGIN + 16, notes_top + 14, "Order Notes", size=9.5, font="F2", color=muted)
        text_block(
            PAGE_MARGIN + 16,
            notes_top + 34,
            order.order_notes,
            CONTENT_WIDTH - 32,
            size=9.5,
            color=text,
            line_height=1.35,
        )
        current_top = notes_top + notes_height

    table_top = current_top + 28
    table_width = CONTENT_WIDTH
    col_item = 276
    col_qty = 56
    col_unit = 92
    col_total = table_width - col_item - col_qty - col_unit

    def draw_table_header(top):
        rect_top(PAGE_MARGIN, top, table_width, 30, fill_color=navy)
        text_top(PAGE_MARGIN + 14, top + 9, "Item", size=10, font="F2", color=(255, 255, 255))
        text_top(PAGE_MARGIN + col_item + 14, top + 9, "Qty", size=10, font="F2", color=(255, 255, 255))
        text_top(PAGE_MARGIN + col_item + col_qty + 14, top + 9, "Unit Price", size=10, font="F2", color=(255, 255, 255))
        text_top(PAGE_MARGIN + col_item + col_qty + col_unit + 14, top + 9, "Line Total", size=10, font="F2", color=(255, 255, 255))
        return top + 30

    if table_top + 72 > PAGE_HEIGHT - 110:
        start_page(include_intro=False)
        cursor_top = draw_table_header(76)
    else:
        cursor_top = draw_table_header(table_top)
    for index, item in enumerate(items, start=1):
        item_lines = _wrap_text(f"{index}. {item.product.name}", col_item - 24, 10.5, bold=True)
        row_height = max(34, 16 + (len(item_lines) * 15))
        if cursor_top + row_height > PAGE_HEIGHT - 110:
            start_page(include_intro=False)
            cursor_top = draw_table_header(76)

        fill_color = (255, 255, 255) if index % 2 else (249, 251, 254)
        rect_top(PAGE_MARGIN, cursor_top, table_width, row_height, fill_color=fill_color, stroke_color=border)
        text_block(PAGE_MARGIN + 14, cursor_top + 10, f"{index}. {item.product.name}", col_item - 24, size=10.5, font="F2", color=text, line_height=1.35)
        text_right(PAGE_MARGIN + col_item + col_qty - 14, cursor_top + 12, str(item.quantity), size=10.5, color=text)
        text_right(PAGE_MARGIN + col_item + col_qty + col_unit - 14, cursor_top + 12, _format_currency(item.price), size=10.5, color=text)
        text_right(PAGE_MARGIN + table_width - 14, cursor_top + 12, _format_currency(item.line_total), size=10.5, font="F2", color=text)
        cursor_top += row_height

    totals_box_height = 156
    support_box_height = 70
    support_gap = 22
    totals_box_top = cursor_top + 26
    if totals_box_top + totals_box_height + support_gap + support_box_height > PAGE_HEIGHT - 84:
        start_page(include_intro=False)
        totals_box_top = 96

    totals_box_width = 252
    totals_box_x = PAGE_WIDTH - PAGE_MARGIN - totals_box_width
    rect_top(totals_box_x, totals_box_top, totals_box_width, totals_box_height, fill_color=card, stroke_color=border)
    text_top(totals_box_x + 18, totals_box_top + 14, "Order Summary", size=9.5, font="F2", color=muted)
    total_rows = [
        ("Subtotal", _format_currency(invoice.subtotal)),
        ("Tax", _format_currency(invoice.tax)),
        ("Shipping", _format_currency(invoice.shipping_cost)),
    ]
    row_top = totals_box_top + 38
    for label, value in total_rows:
        text_top(totals_box_x + 18, row_top, label, size=11, color=muted)
        text_right(totals_box_x + totals_box_width - 18, row_top, value, size=11, font="F2", color=text)
        row_top += 24
    line_top(totals_box_x + 18, row_top + 6, totals_box_x + totals_box_width - 18, row_top + 6, stroke_color=border)
    text_top(totals_box_x + 18, row_top + 18, "Total Amount", size=11.5, font="F2", color=text)
    text_right(
        totals_box_x + totals_box_width - 18,
        row_top + 16,
        _format_currency(invoice.total_amount),
        size=13,
        font="F2",
        color=green,
    )

    note_top = totals_box_top + totals_box_height + support_gap
    if note_top + support_box_height <= PAGE_HEIGHT - 84:
        rect_top(PAGE_MARGIN, note_top, CONTENT_WIDTH, support_box_height, fill_color=gold_soft, stroke_color=border)
        text_top(PAGE_MARGIN + 16, note_top + 14, "Support", size=9.5, font="F2", color=muted)
        text_top(
            PAGE_MARGIN + 16,
            note_top + 34,
            "For invoice support, contact info@etsgrp.in with your invoice number and order reference.",
            size=10,
            color=text,
        )

    return document.render()
