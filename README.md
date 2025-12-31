# WCB Super Advocate (offline-first)

An offline-first assistant to organize Alberta WCB cases, extract text from local documents, and draft neutral letters using local templates. No internet is required and no cloud services are used.

## Quick start (Windows one-click)

1. Install Python 3.11 or newer.
2. Double-click `build_windows.bat`. This installs minimal dependencies and builds `dist\WCB_Super_Advocate.exe`.
3. Double-click `dist\WCB_Super_Advocate.exe` to launch the guided wizard.

Everything stays local: cases are stored under `cases/<case_name>/`, and logs are written to `logs/app.log`.

## How to start a case

1. Choose **“Start new case”** in the wizard.
2. Enter a simple case name (no special characters). Factual-Only Mode is on by default to avoid unverified policy text.
3. The app creates `cases/<case_name>/` with `imports/`, `exports/`, `policy/`, and `notes/`.
4. Follow the prompt: “Next step: import documents.”

## How to import documents

1. Choose **“Import documents”**.
2. Paste the full path to a PDF, DOCX, or TXT file (no internet needed). The file is copied into `cases/<case_name>/imports/`.
3. Pick a tag (decision, medical, correspondence, employer, wage, rtw, or other). Text extraction runs automatically.
4. If a file cannot be read, you’ll see a friendly message and the app keeps running. Errors also log to `logs/app.log`.
5. Next step suggestions guide you to build the timeline or issues.

## How to build the timeline

1. Choose **“Build timeline.”**
2. Enter dates (YYYY-MM-DD) and short descriptions. Optionally link an imported document.
3. Press Enter on an empty date to finish. Entries are saved to `case_state.json` and exported later.

## How to build the issues list

1. Choose **“Build issues list.”**
2. Add concise, neutral issue titles and concerns (e.g., “Clarify wage recalculation”).
3. Link documents if helpful, or skip. Press Enter on an empty title to finish.

## How to draft letters

1. Choose **“Draft appeal/review/disclosure letter.”**
2. Pick one of the local templates:
   - Appeal/Review submission skeleton
   - Fairness Review letter skeleton
   - Disclosure request letter skeleton
3. Drafts use only the timeline, issues, and policy files in your case `policy/` folder. If no policy text is available, the draft states “Policy source not provided yet.”
4. Outputs are saved to `cases/<case_name>/exports/` as both `.txt` and `.docx`.

## How to export drafts and checklists

1. Choose **“Export package (TXT + DOCX + JSON).”**
2. The app writes:
   - `timeline_<timestamp>.txt` and `.json`
   - `issues_<timestamp>.txt` and `.json`
   - `contradictions_checklist_<timestamp>.txt`
3. Review everything in `cases/<case_name>/exports/`.

## Development (optional)

- Run from source on Windows: double-click `run_dev.bat`.
- On other platforms:
  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  python -m wcb_app.main wizard
  ```
- Diagnostics command: `python -m wcb_app.main diagnostics`

## Templates and samples

- Templates live in `templates/`:
  - `appeal_submission.j2`
  - `fairness_review.j2`
  - `disclosure_request.j2`
- A tiny demo case is in `sample_cases/demo_case/`. Copy it into `cases/` if you want to explore before adding your own data.

## Safety and scope

- Offline-first; no network access required.
- No legal advice. Drafts include a reminder to stay neutral (“I’m concerned that…”, “It appears…”).
- No requests for SIN or banking info.
- Policy text is only cited if stored in the local `policy/` folder or supplied by you. Otherwise the app states: “Policy source not provided yet.”
