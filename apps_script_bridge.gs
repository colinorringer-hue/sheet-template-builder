/**
 * OPTIONAL ZERO-BILLING BRIDGE
 *
 * Deploy this as an Apps Script Web App. It receives one JSON request from the
 * Streamlit app, creates a Google Sheet in the account running the web app,
 * and formats whole ranges (not cell-by-cell loops).
 *
 * Before deploying, add a Script Property named TEMPLATE_BUILDER_SECRET.
 */

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents || '{}');
    const expected = PropertiesService.getScriptProperties().getProperty('TEMPLATE_BUILDER_SECRET');
    if (!expected || body.secret !== expected) {
      return jsonResponse_({ok: false, error: 'Unauthorized'});
    }

    const c = body.config || {};
    const headers = (c.headers || ['HEADER']).map(h => c.uppercase_headers ? String(h).toUpperCase() : String(h));
    const cols = Math.max(1, headers.length);
    const rows = Math.max(1, Number(c.body_rows || 30));

    const ss = SpreadsheetApp.create(c.spreadsheet_title || 'New Template', rows + 3, cols);
    const sh = ss.getSheets()[0];
    sh.setName((c.sheet_name || 'Sheet1').substring(0, 100));
    sh.setHiddenGridlines(true);

    if (cols > 1) {
      sh.getRange(1, 1, 1, cols).merge();
      sh.getRange(2, 1, 1, cols).merge();
    }

    sh.getRange(1, 1).setValue(c.title || '');
    sh.getRange(2, 1).setValue(c.subtitle || '');
    sh.getRange(3, 1, 1, cols).setValues([headers]);

    sh.getRange(1, 1, 1, cols)
      .setBackground(c.title_bg).setFontColor(c.title_fg).setFontFamily(c.font_family)
      .setFontSize(Number(c.title_size)).setFontWeight('bold').setHorizontalAlignment('center').setVerticalAlignment('middle');

    sh.getRange(2, 1, 1, cols)
      .setBackground(c.subtitle_bg).setFontColor(c.subtitle_fg).setFontFamily(c.font_family)
      .setFontSize(Number(c.subtitle_size)).setHorizontalAlignment('center').setVerticalAlignment('middle');

    sh.getRange(3, 1, 1, cols)
      .setBackground(c.header_bg).setFontColor(c.header_fg).setFontFamily(c.font_family)
      .setFontSize(Number(c.header_size)).setFontWeight('bold').setHorizontalAlignment('center')
      .setVerticalAlignment('middle').setWrap(true)
      .setBorder(null, null, true, null, null, null, '#000000', SpreadsheetApp.BorderStyle.SOLID_THICK);

    const bodyRange = sh.getRange(4, 1, rows, cols);
    bodyRange.setBackground(c.body_bg).setFontColor(c.body_fg).setFontFamily(c.font_family)
      .setFontSize(Number(c.body_size)).setVerticalAlignment('middle').setWrap(true);

    if (c.alternating_rows) {
      for (let r = 4; r < 4 + rows; r += 2) {
        sh.getRange(r, 1, 1, cols).setBackground('#F5F5F5');
      }
    }

    const p = c.border_preset || 'None';
    if (p === 'Solid Gridlines') {
      bodyRange.setBorder(true, true, true, true, true, true, '#000000', SpreadsheetApp.BorderStyle.SOLID);
    } else if (p === 'Solid Horizontal') {
      bodyRange.setBorder(true, false, true, false, true, false, '#000000', SpreadsheetApp.BorderStyle.SOLID);
    } else if (p === 'Dotted Vertical + Solid Horizontal') {
      bodyRange.setBorder(true, true, true, true, true, true, '#000000', SpreadsheetApp.BorderStyle.DOTTED);
      // Reinforce top/bottom with solid borders.
      bodyRange.setBorder(true, null, true, null, null, null, '#000000', SpreadsheetApp.BorderStyle.SOLID);
    } else if (p === 'Thick Outside Border') {
      bodyRange.setBorder(true, true, true, true, false, false, '#000000', SpreadsheetApp.BorderStyle.SOLID_THICK);
    }

    sh.setRowHeight(1, Number(c.title_row_height || 44));
    sh.setRowHeight(2, Number(c.subtitle_row_height || 28));
    sh.setRowHeight(3, Number(c.header_row_height || 34));
    sh.setRowHeights(4, rows, Number(c.body_row_height || 28));
    const widthMap = {Small: 90, Medium: 125, Large: 165};
    sh.setColumnWidths(1, cols, widthMap[c.column_size] || 125);

    if (c.freeze_headers) sh.setFrozenRows(3);

    if (c.filter_headers) {
      // Filter range includes the header row plus all configured body rows.
      sh.getRange(3, 1, rows + 1, cols).createFilter();
    }

    // Optional logos: decode the uploaded image data and anchor each image to
    // the appropriate top-row cell. These are native Google Sheets images, so
    // they avoid the #VALUE! issue caused by importing Excel cell-image formulas.
    if (body.left_logo_base64) {
      const blob = Utilities.newBlob(
        Utilities.base64Decode(body.left_logo_base64),
        body.left_logo_mime || 'image/png',
        'left_logo'
      );
      const img = sh.insertImage(blob, 1, 1);
      fitImageToCell_(img, sh, 1, 1);
    }
    if (body.right_logo_base64) {
      const blob = Utilities.newBlob(
        Utilities.base64Decode(body.right_logo_base64),
        body.right_logo_mime || 'image/png',
        'right_logo'
      );
      const img = sh.insertImage(blob, cols, 1);
      fitImageToCell_(img, sh, cols, 1);
    }

    SpreadsheetApp.flush();
    return jsonResponse_({ok: true, id: ss.getId(), url: ss.getUrl(), name: ss.getName()});
  } catch (err) {
    return jsonResponse_({ok: false, error: String(err && err.message ? err.message : err)});
  }
}

function fitImageToCell_(img, sh, col, row) {
  const cellWidth = sh.getColumnWidth(col);
  const cellHeight = sh.getRowHeight(row);
  const maxW = Math.max(20, cellWidth - 12);
  const maxH = Math.max(20, cellHeight - 8);
  const w = img.getWidth();
  const h = img.getHeight();
  const scale = Math.min(maxW / w, maxH / h, 1);
  const newW = Math.max(1, Math.round(w * scale));
  const newH = Math.max(1, Math.round(h * scale));
  img.setWidth(newW).setHeight(newH);
  img.setAnchorCell(sh.getRange(row, col));
  img.setAnchorCellXOffset(Math.max(0, Math.round((cellWidth - newW) / 2)));
  img.setAnchorCellYOffset(Math.max(0, Math.round((cellHeight - newH) / 2)));
}

function jsonResponse_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
