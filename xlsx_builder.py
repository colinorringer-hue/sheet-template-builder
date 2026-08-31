from __future__ import annotations

from io import BytesIO
from typing import Optional

import xlsxwriter
from PIL import Image


def _xlsx_color(hex_color: str) -> str:
    value = (hex_color or "#FFFFFF").strip()
    if not value.startswith("#"):
        value = "#" + value
    return value.upper()


def _column_width(header: str, size: str) -> float:
    """Choose a Google-Sheets-friendly width using a simple S/M/L control."""
    text = (header or "").strip().upper()
    base = {"Small": 11.0, "Medium": 15.0, "Large": 20.0}.get(size, 15.0)

    wide_terms = {
        "NOTES", "OFFERS", "STRENGTHS", "CONCERNS", "PROJECTION", "NEXT STEP",
        "DECISION", "TENDENCY", "CONCEPT", "FORMATION", "PERSONNEL", "STATUS",
    }
    extra_wide_terms = {"NOTES", "STRENGTHS", "CONCERNS", "PROJECTION", "OFFERS"}
    compact_terms = {"#", "ST", "YR", "WT", "HT", "POS", "FIT", "GRADE"}

    if text in extra_wide_terms:
        width = base * 1.8
    elif text in wide_terms:
        width = base * 1.45
    elif text in compact_terms:
        width = base * 0.8
    else:
        width = max(base, len(text) + 3.0)

    return max(8.0, min(38.0, width))


def _prepare_logo(data: Optional[bytes], max_width: int = 110, max_height: int = 42):
    """Normalize an uploaded logo to PNG while preserving aspect ratio."""
    if not data:
        return None

    image = Image.open(BytesIO(data)).convert("RGBA")

    # Remove transparent padding when present so the visible logo gets the full box.
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox:
        image = image.crop(bbox)

    image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    out = BytesIO()
    image.save(out, format="PNG", optimize=True)
    out.seek(0)
    return out.getvalue(), image.width, image.height



def build_xlsx(cfg: dict, left_logo: Optional[bytes] = None, right_logo: Optional[bytes] = None) -> bytes:
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    worksheet = workbook.add_worksheet((cfg.get("sheet_name") or "Sheet1")[:31])

    headers = [h.strip() for h in cfg.get("headers", []) if h.strip()]
    if cfg.get("uppercase_headers"):
        headers = [h.upper() for h in headers]
    if not headers:
        headers = ["HEADER"]

    num_cols = len(headers)
    body_rows = max(1, int(cfg.get("body_rows", 30)))
    column_size = cfg.get("column_size", "Medium")
    col_widths = [_column_width(h, column_size) for h in headers]

    title_fmt = workbook.add_format({
        "font_name": cfg["font_family"],
        "font_size": int(cfg["title_size"]),
        "bold": True,
        "font_color": _xlsx_color(cfg["title_fg"]),
        "bg_color": _xlsx_color(cfg["title_bg"]),
        "align": "center",
        "valign": "vcenter",
    })
    subtitle_fmt = workbook.add_format({
        "font_name": cfg["font_family"],
        "font_size": int(cfg["subtitle_size"]),
        "font_color": _xlsx_color(cfg["subtitle_fg"]),
        "bg_color": _xlsx_color(cfg["subtitle_bg"]),
        "align": "center",
        "valign": "vcenter",
    })
    header_fmt = workbook.add_format({
        "font_name": cfg["font_family"],
        "font_size": int(cfg["header_size"]),
        "bold": True,
        "font_color": _xlsx_color(cfg["header_fg"]),
        "bg_color": _xlsx_color(cfg["header_bg"]),
        "align": "center",
        "valign": "vcenter",
        "text_wrap": True,
        "bottom": 2,
    })

    body_base = {
        "font_name": cfg["font_family"],
        "font_size": int(cfg["body_size"]),
        "font_color": _xlsx_color(cfg["body_fg"]),
        "bg_color": _xlsx_color(cfg["body_bg"]),
        "valign": "vcenter",
        "text_wrap": True,
    }

    border_preset = cfg.get("border_preset", "None")
    if border_preset == "Solid Gridlines":
        body_base.update({"border": 1})
    elif border_preset == "Solid Horizontal":
        body_base.update({"top": 1, "bottom": 1})
    elif border_preset == "Dotted Vertical + Solid Horizontal":
        body_base.update({"top": 1, "bottom": 1, "left": 3, "right": 3})

    body_fmt = workbook.add_format(body_base)
    alt_base = dict(body_base)
    alt_base["bg_color"] = "#F5F5F5"
    alt_fmt = workbook.add_format(alt_base)

    has_left_logo = bool(left_logo)
    has_right_logo = bool(right_logo)

    # Row 1 is a real cell-based header. When a logo is uploaded, its edge cell is
    # kept unmerged so Excel/Google Sheets can treat the image as belonging to that
    # cell rather than as a floating drawing over a merged title range.
    if num_cols >= 3 and (has_left_logo or has_right_logo):
        title_start = 1 if has_left_logo else 0
        title_end = num_cols - 2 if has_right_logo else num_cols - 1

        if has_left_logo:
            worksheet.write_blank(0, 0, None, title_fmt)
        if has_right_logo:
            worksheet.write_blank(0, num_cols - 1, None, title_fmt)

        if title_start < title_end:
            worksheet.merge_range(0, title_start, 0, title_end, cfg.get("title", ""), title_fmt)
        elif title_start == title_end:
            worksheet.write(0, title_start, cfg.get("title", ""), title_fmt)
    elif num_cols > 1:
        worksheet.merge_range(0, 0, 0, num_cols - 1, cfg.get("title", ""), title_fmt)
    else:
        worksheet.write(0, 0, cfg.get("title", ""), title_fmt)

    if num_cols > 1:
        worksheet.merge_range(1, 0, 1, num_cols - 1, cfg.get("subtitle", ""), subtitle_fmt)
    else:
        worksheet.write(1, 0, cfg.get("subtitle", ""), subtitle_fmt)

    for col, header in enumerate(headers):
        worksheet.write(2, col, header, header_fmt)

    for r in range(3, 3 + body_rows):
        row_fmt = alt_fmt if cfg.get("alternating_rows") and (r - 3) % 2 == 1 else body_fmt
        for c in range(num_cols):
            worksheet.write_blank(r, c, None, row_fmt)

    if border_preset == "Thick Outside Border":
        top = workbook.add_format({**body_base, "top": 2})
        bottom = workbook.add_format({**body_base, "bottom": 2})
        left = workbook.add_format({**body_base, "left": 2})
        right = workbook.add_format({**body_base, "right": 2})
        tl = workbook.add_format({**body_base, "top": 2, "left": 2})
        tr = workbook.add_format({**body_base, "top": 2, "right": 2})
        bl = workbook.add_format({**body_base, "bottom": 2, "left": 2})
        br = workbook.add_format({**body_base, "bottom": 2, "right": 2})
        start, end = 3, 3 + body_rows - 1
        for c in range(num_cols):
            worksheet.write_blank(start, c, None, top)
            worksheet.write_blank(end, c, None, bottom)
        for r in range(start, end + 1):
            worksheet.write_blank(r, 0, None, left)
            worksheet.write_blank(r, num_cols - 1, None, right)
        worksheet.write_blank(start, 0, None, tl)
        worksheet.write_blank(start, num_cols - 1, None, tr)
        worksheet.write_blank(end, 0, None, bl)
        worksheet.write_blank(end, num_cols - 1, None, br)

    # Automatic sizing. IMPORTANT: only the actual table columns are touched.
    # Older versions formatted/hidden columns all the way through XFD; Google Sheets
    # interpreted those as real blank columns on import.
    worksheet.set_row(0, 36)
    worksheet.set_row(1, 21)
    worksheet.set_row(2, 26)
    for r in range(3, 3 + body_rows):
        worksheet.set_row(r, 21)
    for c, width in enumerate(col_widths):
        worksheet.set_column(c, c, width)

    if cfg.get("freeze_headers"):
        # The column header is row 3. Freezing it necessarily freezes title/subtitle too.
        worksheet.freeze_panes(3, 0)

    if cfg.get("filter_headers"):
        # Apply AutoFilter across the header plus the configured blank body rows.
        # The header is Excel row 3 (zero-based row index 2).
        worksheet.autofilter(2, 0, 2 + body_rows, num_cols - 1)

    # Standard Excel drawing images are much more compatible with Google Sheets
    # imports than Excel's newer "Place in Cell" image format. Keep each image
    # anchored to the top-left or top-right table cell and size it to stay inside
    # that cell. object_position=1 means move and size with cells.
    if left_logo:
        cell_px = max(45, int(col_widths[0] * 7 + 5))
        prepared_left = _prepare_logo(left_logo, max_width=max(24, cell_px - 12), max_height=34)
        if prepared_left:
            logo_bytes, logo_w, logo_h = prepared_left
            x_offset = max(2, int((cell_px - logo_w) / 2))
            y_offset = max(1, int((36 - logo_h) / 2))
            worksheet.insert_image(
                0, 0, "left_logo.png",
                {
                    "image_data": BytesIO(logo_bytes),
                    "x_offset": x_offset,
                    "y_offset": y_offset,
                    "object_position": 1,
                    "description": "Left logo",
                },
            )

    if right_logo:
        anchor_col = num_cols - 1
        cell_px = max(45, int(col_widths[anchor_col] * 7 + 5))
        prepared_right = _prepare_logo(right_logo, max_width=max(24, cell_px - 12), max_height=34)
        if prepared_right:
            logo_bytes, logo_w, logo_h = prepared_right
            x_offset = max(2, int((cell_px - logo_w) / 2))
            y_offset = max(1, int((36 - logo_h) / 2))
            worksheet.insert_image(
                0, anchor_col, "right_logo.png",
                {
                    "image_data": BytesIO(logo_bytes),
                    "x_offset": x_offset,
                    "y_offset": y_offset,
                    "object_position": 1,
                    "description": "Right logo",
                },
            )

    # Excel itself always has columns through XFD. Hide everything after the
    # table so the downloaded workbook visually ends at the last table column.
    # Google Sheets may choose not to preserve hidden unused columns on import;
    # the optional Apps Script output creates the native sheet with an exact
    # column count instead.
    if num_cols < 16384:
        worksheet.set_column(num_cols, 16383, 0, None, {"hidden": True})

    worksheet.hide_gridlines(2)
    worksheet.set_zoom(90)

    workbook.close()
    return output.getvalue()
