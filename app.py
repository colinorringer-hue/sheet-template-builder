from __future__ import annotations

import base64
import html
import re

import requests
import streamlit as st

from presets import PRESETS, TEMPLATE_TYPES
from xlsx_builder import build_xlsx

st.set_page_config(page_title="Google Sheets Template Builder", page_icon="📊", layout="wide")


def get_secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default)).strip()
    except Exception:
        return default


def require_passcode() -> None:
    configured = get_secret("APP_PASSCODE")
    if not configured or st.session_state.get("authenticated"):
        return
    st.title("Template Builder")
    entered = st.text_input("Passcode", type="password")
    if st.button("Enter", type="primary", use_container_width=True):
        if entered == configured:
            st.session_state["authenticated"] = True
            st.rerun()
        st.error("Incorrect passcode.")
    st.stop()


def bridge_settings() -> tuple[str, str]:
    return get_secret("APPS_SCRIPT_URL"), get_secret("APPS_SCRIPT_SECRET")


def logo_data_uri(upload) -> str | None:
    if not upload:
        return None
    mime = upload.type or "image/png"
    encoded = base64.b64encode(upload.getvalue()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def border_css(preset: str, row_index: int, total_rows: int, col_index: int, total_cols: int) -> str:
    if preset == "Solid Gridlines":
        return "border:1px solid #B8B8B8;"
    if preset == "Solid Horizontal":
        return "border-top:1px solid #B8B8B8;border-bottom:1px solid #B8B8B8;"
    if preset == "Dotted Vertical + Solid Horizontal":
        return "border-top:1px solid #B8B8B8;border-bottom:1px solid #B8B8B8;border-left:1px dotted #B8B8B8;border-right:1px dotted #B8B8B8;"
    if preset == "Thick Outside Border":
        pieces = []
        if row_index == 0:
            pieces.append("border-top:2px solid #555;")
        if row_index == total_rows - 1:
            pieces.append("border-bottom:2px solid #555;")
        if col_index == 0:
            pieces.append("border-left:2px solid #555;")
        if col_index == total_cols - 1:
            pieces.append("border-right:2px solid #555;")
        return "".join(pieces)
    return ""


require_passcode()

st.title("Google Sheets Template Builder")
st.caption(
    "Build a polished spreadsheet template in Python with no Google Cloud billing. "
    "Preview the full table, download it, then open/import it in Google Sheets."
)

with st.sidebar:
    st.header("Starting Point")
    template_type = st.selectbox("Template type", list(TEMPLATE_TYPES.keys()))
    preset_name = st.selectbox("Style preset", list(PRESETS.keys()))
    preset = PRESETS[preset_name]
    st.divider()
    st.markdown("**Output**")
    output_mode = st.radio(
        "Choose output",
        ["Download .xlsx", "Create Google Sheet via Apps Script"],
        help="The .xlsx option needs no Google setup. The free Apps Script option creates a native Google Sheet with exactly the number of table columns you chose.",
    )

left, right = st.columns([1.2, 1])

with left:
    st.subheader("Content")
    spreadsheet_title = st.text_input("File name", value="New Template")
    sheet_name = st.text_input("Sheet/tab name", value="Sheet1")
    title = st.text_input("Title", value="TITLE")
    subtitle = st.text_input("Subtitle", value="SUBTITLE")
    default_header_text = "\n".join(TEMPLATE_TYPES[template_type])
    header_text = st.text_area(
        "Column names — one per line",
        value=default_header_text,
        height=230,
        placeholder="POS\nPLAYER\nSCHOOL\nGRADE\nNOTES",
    )
    headers = [x.strip() for x in header_text.splitlines() if x.strip()]
    body_rows = st.number_input("Blank body rows", min_value=1, max_value=1000, value=30, step=1)

with right:
    st.subheader("Style")
    c1, c2 = st.columns(2)
    with c1:
        title_bg = st.color_picker("Title background", preset["title_bg"])
        title_fg = st.color_picker("Title text", preset["title_fg"])
        header_bg = st.color_picker("Header background", preset["header_bg"])
        header_fg = st.color_picker("Header text", preset["header_fg"])
    with c2:
        subtitle_bg = st.color_picker("Subtitle background", preset["subtitle_bg"])
        subtitle_fg = st.color_picker("Subtitle text", preset["subtitle_fg"])
        body_bg = st.color_picker("Body background", preset["body_bg"])
        body_fg = st.color_picker("Body text", preset["body_fg"])

    fonts = ["Chakra Petch", "Arial", "Roboto", "Montserrat", "Oswald", "Georgia"]
    font_index = fonts.index(preset["font_family"]) if preset["font_family"] in fonts else 0
    font_family = st.selectbox("Font", fonts, index=font_index)

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        title_size = st.number_input("Title size", 8, 36, preset["title_size"])
    with s2:
        subtitle_size = st.number_input("Subtitle size", 8, 24, preset["subtitle_size"])
    with s3:
        header_size = st.number_input("Header size", 8, 24, preset["header_size"])
    with s4:
        body_size = st.number_input("Body size", 8, 24, preset["body_size"])

st.divider()
a, b = st.columns([1, 1])

with a:
    st.subheader("Borders & Behavior")
    border_options = [
        "Dotted Vertical + Solid Horizontal",
        "Solid Horizontal",
        "Thick Outside Border",
        "Solid Gridlines",
        "None",
    ]
    border_preset = st.selectbox(
        "Border preset",
        border_options,
        index=border_options.index(preset["border_preset"]),
    )
    uppercase_headers = st.checkbox("Uppercase headers", value=preset["uppercase_headers"])
    freeze_headers = st.checkbox(
        "Freeze header",
        value=preset["freeze_headers"],
        help="Keeps the title, subtitle, and column-header row visible while you scroll. Google Sheets freezes the rows above the header too.",
    )
    filter_headers = st.checkbox(
        "Filter header",
        value=True,
        help="Adds filter dropdowns to every column header so the finished sheet can be sorted and filtered immediately.",
    )
    alternating_rows = st.checkbox("Alternating body rows", value=False)
    column_size = st.segmented_control("Column size", ["Small", "Medium", "Large"], default="Medium")
    st.caption("Medium is the default. Text-heavy fields like NOTES and PROJECTION automatically get extra room.")

with b:
    st.subheader("Logos")
    st.caption("Upload PNG/JPG logos. They are embedded directly into the downloaded spreadsheet.")
    logo_left_col, logo_right_col = st.columns(2)
    with logo_left_col:
        left_logo_upload = st.file_uploader("Left logo", type=["png", "jpg", "jpeg"], key="left_logo")
        if left_logo_upload:
            st.image(left_logo_upload, width=120)
    with logo_right_col:
        right_logo_upload = st.file_uploader("Right logo", type=["png", "jpg", "jpeg"], key="right_logo")
        if right_logo_upload:
            st.image(right_logo_upload, width=120)

cfg = {
    "spreadsheet_title": spreadsheet_title.strip() or "New Template",
    "sheet_name": sheet_name.strip() or "Sheet1",
    "title": title,
    "subtitle": subtitle,
    "headers": headers or ["HEADER"],
    "body_rows": int(body_rows),
    "title_bg": title_bg,
    "title_fg": title_fg,
    "subtitle_bg": subtitle_bg,
    "subtitle_fg": subtitle_fg,
    "header_bg": header_bg,
    "header_fg": header_fg,
    "body_bg": body_bg,
    "body_fg": body_fg,
    "font_family": font_family,
    "title_size": int(title_size),
    "subtitle_size": int(subtitle_size),
    "header_size": int(header_size),
    "body_size": int(body_size),
    "border_preset": border_preset,
    "uppercase_headers": uppercase_headers,
    "freeze_headers": freeze_headers,
    "filter_headers": filter_headers,
    "alternating_rows": alternating_rows,
    "column_size": column_size or "Medium",
}

st.divider()
st.subheader("Full Table Preview")
st.caption("Scroll horizontally or vertically to inspect the entire template. The preview uses all of your configured blank rows.")

preview_headers = [h.upper() if uppercase_headers else h for h in (headers or ["HEADER"])]
num_preview_cols = len(preview_headers)
preview_body_rows = int(body_rows)
preview_col_widths = {"Small": 92, "Medium": 125, "Large": 165}
min_col_width = preview_col_widths.get(column_size or "Medium", 125)
preview_width = max(760, num_preview_cols * min_col_width)
left_logo_uri = logo_data_uri(left_logo_upload)
right_logo_uri = logo_data_uri(right_logo_upload)

logo_left_html = (
    f'<img src="{left_logo_uri}" style="max-height:42px;max-width:calc(100% - 8px);object-fit:contain;">'
    if left_logo_uri
    else ""
)
logo_right_html = (
    f'<img src="{right_logo_uri}" style="max-height:42px;max-width:calc(100% - 8px);object-fit:contain;">'
    if right_logo_uri
    else ""
)

edge_cell_width = min_col_width
if num_preview_cols >= 3 and (left_logo_uri or right_logo_uri):
    preview_html = f'''
<div style="border:1px solid #CFCFCF;border-radius:6px;overflow:auto;max-height:620px;background:white;">
  <div style="min-width:{preview_width}px;font-family:'{html.escape(font_family)}',Arial,sans-serif;">
    <div style="display:grid;grid-template-columns:{edge_cell_width}px 1fr {edge_cell_width}px;min-height:54px;background:{title_bg};color:{title_fg};box-sizing:border-box;">
      <div style="border-right:1px solid rgba(255,255,255,.18);display:flex;align-items:center;justify-content:center;padding:4px;box-sizing:border-box;overflow:hidden;">{logo_left_html}</div>
      <div style="display:flex;align-items:center;justify-content:center;text-align:center;padding:8px;font-size:{title_size}px;font-weight:700;box-sizing:border-box;">{html.escape(title) if title else '&nbsp;'}</div>
      <div style="border-left:1px solid rgba(255,255,255,.18);display:flex;align-items:center;justify-content:center;padding:4px;box-sizing:border-box;overflow:hidden;">{logo_right_html}</div>
    </div>
    <div style="background:{subtitle_bg};color:{subtitle_fg};font-size:{subtitle_size}px;text-align:center;padding:6px 8px;min-height:30px;box-sizing:border-box;">
      {html.escape(subtitle) if subtitle else '&nbsp;'}
    </div>
    <table style="width:100%;border-collapse:collapse;table-layout:fixed;background:{body_bg};color:{body_fg};font-size:{body_size}px;">
      <thead>
        <tr>
'''
else:
    preview_html = f'''
<div style="border:1px solid #CFCFCF;border-radius:6px;overflow:auto;max-height:620px;background:white;">
  <div style="min-width:{preview_width}px;font-family:'{html.escape(font_family)}',Arial,sans-serif;">
    <div style="background:{title_bg};color:{title_fg};font-size:{title_size}px;font-weight:700;text-align:center;padding:10px 8px;min-height:48px;display:flex;align-items:center;justify-content:center;box-sizing:border-box;">
      <span>{html.escape(title) if title else '&nbsp;'}</span>
    </div>
    <div style="background:{subtitle_bg};color:{subtitle_fg};font-size:{subtitle_size}px;text-align:center;padding:6px 8px;min-height:30px;box-sizing:border-box;">
      {html.escape(subtitle) if subtitle else '&nbsp;'}
    </div>
    <table style="width:100%;border-collapse:collapse;table-layout:fixed;background:{body_bg};color:{body_fg};font-size:{body_size}px;">
      <thead>
        <tr>
'''
for h in preview_headers:
    preview_html += (
        f'<th style="min-width:{min_col_width}px;background:{header_bg};color:{header_fg};'
        f'font-size:{header_size}px;font-weight:700;text-align:center;padding:7px 8px;'
        f'border-bottom:3px solid #666;border-left:1px solid #B8B8B8;border-right:1px solid #B8B8B8;'
        f'box-sizing:border-box;white-space:normal;">{html.escape(h)}'
        f'{" <span style=\"font-size:0.75em;opacity:.75;\">▼</span>" if filter_headers else ""}</th>'
    )
preview_html += "</tr></thead><tbody>"

for r in range(preview_body_rows):
    row_bg = "#F5F5F5" if alternating_rows and r % 2 == 1 else body_bg
    preview_html += f'<tr style="background:{row_bg};">'
    for c in range(num_preview_cols):
        cell_border = border_css(border_preset, r, preview_body_rows, c, num_preview_cols)
        preview_html += (
            f'<td style="height:28px;padding:4px 7px;box-sizing:border-box;{cell_border}">&nbsp;</td>'
        )
    preview_html += "</tr>"

preview_html += "</tbody></table></div></div>"
st.markdown(preview_html, unsafe_allow_html=True)

left_bytes = left_logo_upload.getvalue() if left_logo_upload else None
right_bytes = right_logo_upload.getvalue() if right_logo_upload else None

try:
    xlsx_bytes = build_xlsx(cfg, left_bytes, right_bytes)
except Exception as exc:
    st.error(f"Could not build spreadsheet: {exc}")
    st.stop()

safe_name = re.sub(r'[^A-Za-z0-9 _.-]+', '', cfg["spreadsheet_title"]).strip() or "template"
filename = f"{safe_name}.xlsx"

if output_mode == "Download .xlsx":
    st.download_button(
        "DOWNLOAD TEMPLATE",
        data=xlsx_bytes,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
    )
    st.info("After downloading: upload the .xlsx to Google Drive → open it with Google Sheets. The workbook hides columns after your table, but Google Sheets may add/show unused columns during import. For an exact A:last-column native sheet, use the free Apps Script output option.")
else:
    bridge_url, bridge_secret = bridge_settings()
    if not bridge_url or not bridge_secret:
        st.warning("The optional Apps Script bridge is not configured yet. The download option already works with zero Google setup.")
        st.code('APPS_SCRIPT_URL = "https://script.google.com/macros/s/.../exec"\nAPPS_SCRIPT_SECRET = "choose-a-long-random-secret"', language="toml")
    else:
        if st.button("CREATE GOOGLE SHEET", type="primary", use_container_width=True):
            with st.spinner("Creating Google Sheet..."):
                try:
                    payload = {"secret": bridge_secret, "config": cfg}
                    if left_logo_upload:
                        payload["left_logo_base64"] = base64.b64encode(left_logo_upload.getvalue()).decode("ascii")
                        payload["left_logo_mime"] = left_logo_upload.type or "image/png"
                    if right_logo_upload:
                        payload["right_logo_base64"] = base64.b64encode(right_logo_upload.getvalue()).decode("ascii")
                        payload["right_logo_mime"] = right_logo_upload.type or "image/png"
                    response = requests.post(bridge_url, json=payload, timeout=60)
                    response.raise_for_status()
                    result = response.json()
                    if not result.get("ok"):
                        raise RuntimeError(result.get("error", "Unknown bridge error"))
                    st.success("Google Sheet created.")
                    st.link_button("OPEN GOOGLE SHEET", result["url"], type="primary", use_container_width=True)
                except Exception as exc:
                    st.error(f"Apps Script bridge error: {exc}")
