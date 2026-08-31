# Google Sheets Template Builder

This version does **not** require Google Cloud, a service account, a billing account, or Google API credentials.

## Default workflow — completely free

1. Run or host the Streamlit app.
2. Build the template visually.
3. Click **DOWNLOAD TEMPLATE**.
4. Upload the `.xlsx` file to Google Drive.
5. Open it with Google Sheets.
6. Share the Google Sheet normally.

The workbook is generated in Python, so Apps Script is not involved in the formatting step. Logos are embedded directly into the spreadsheet file.

## Features

- custom title and subtitle
- separate title/subtitle/header/body colors
- Chakra Petch and other fonts
- custom column names
- preset template types
- recruiting/scouting/analytics presets
- row heights and column widths
- frozen header area
- alternating rows
- border presets
- left/right logo uploads
- local visual preview
- optional passcode
- optional one-click Apps Script bridge

## Run locally

Open the project folder in VS Code, then use **Terminal → New Terminal**.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

No Google setup is required for the normal download workflow.

## Share it with everyone for free

The easiest deployment is Streamlit Community Cloud:

1. Create a GitHub repository.
2. Upload these project files to the repository.
3. Go to `share.streamlit.io`.
4. Create an app from the repository.
5. Select `app.py` as the entrypoint.
6. Deploy.

The result is a shareable `*.streamlit.app` URL. Users do not need Python or VS Code.

If you use a private GitHub repository, Streamlit Community Cloud can still deploy it after you grant repository access.

## Optional app passcode

Copy `.streamlit/secrets.example.toml` to `.streamlit/secrets.toml` and set:

```toml
APP_PASSCODE = "your-passcode"
```

When deployed, put this value into the Streamlit app's Secrets settings instead of committing the real file to GitHub.

## Optional: one-click creation in Google Drive

The project includes `apps_script_bridge.gs`.

This is optional. The normal `.xlsx` workflow is already complete.

If you want a **CREATE GOOGLE SHEET** button that creates the file directly in Drive:

1. Go to `script.google.com` and create a new Apps Script project.
2. Replace the default code with the contents of `apps_script_bridge.gs`.
3. Open **Project Settings → Script Properties**.
4. Add a property named `TEMPLATE_BUILDER_SECRET` with a long random secret value.
5. Click **Deploy → New deployment → Web app**.
6. Choose who can access the web app based on your organization needs.
7. Copy the deployed `/exec` URL.
8. In your Streamlit secrets, add:

```toml
APPS_SCRIPT_URL = "YOUR_WEB_APP_EXEC_URL"
APPS_SCRIPT_SECRET = "THE_SAME_RANDOM_SECRET"
```

The Streamlit server then sends one JSON payload to Apps Script. Apps Script creates the Google Sheet and formats whole ranges rather than using the original interactive Apps Script template-builder UI.

## Files

```text
google_sheets_template_builder/
├── app.py
├── xlsx_builder.py
├── presets.py
├── apps_script_bridge.gs
├── requirements.txt
├── README.md
├── Dockerfile
├── .gitignore
└── .streamlit/
    ├── config.toml
    └── secrets.example.toml
```

## Recommended order

Start with the `.xlsx` download workflow and get the design exactly right. After that, turn on the Apps Script bridge only if the extra one-click Drive creation is worth it.


## V5 logo behavior
Uploaded logos use Excel Place in Cell behavior: left in A1, right in the last top-row table cell.

## V6 compatibility notes
- Downloaded `.xlsx` files use standard embedded Excel images anchored to the first and last top-row table cells. This is more compatible with Google Sheets than Excel's newer in-cell image format.
- Excel worksheets always contain the full Excel grid internally. The builder hides every column after the final table column in the downloaded workbook.
- Google Sheets may ignore hidden unused Excel columns when importing `.xlsx` files. If you need a native Google Sheet whose grid is literally A:E for a five-column table, use the optional **Create exact-size Google Sheet via Apps Script** output. Apps Script creates the spreadsheet with exactly the requested number of columns and does not require Google Cloud billing.


## V7

- Added an independent **Filter header** option. When enabled, the .xlsx export gets Excel AutoFilter dropdowns on the header row, and the optional Apps Script output creates a native Google Sheets filter over the same table range.
