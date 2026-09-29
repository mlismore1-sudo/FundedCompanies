# Companies House Investment Monitor

A low-cost MVP that listens to Companies House filing-history and PSC-related streams, enriches relevant events through the REST API, stores them in Supabase Postgres, and displays them in Streamlit.

## What it detects

- SH01 filings.
- PSC stream events.
- PSC-statement stream events.
- Company name, SIC codes and incorporation date through company-profile enrichment.
- A basic event classification such as `SH01 only` or `SH01 + new PSC/RLE`.

## What it does not prove

An SH01 is evidence of a share allotment, not proof that a VC or PE investment occurred. Further document parsing and investor-entity enrichment can be added later.

## Local setup

1. Create a Companies House account and register an application with REST and Streaming API credentials.
2. Create a Supabase project.
3. Run `sql/schema.sql` in the Supabase SQL editor.
4. Create a local virtual environment:

   ```bash
   python -m venv .venv
   ```

5. Activate it:

   macOS/Linux:

   ```bash
   source .venv/bin/activate
   ```

   Windows PowerShell:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

6. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

7. Copy `.env.example` to `.env` and add credentials.
8. Start one worker in a terminal:

   ```bash
   python worker.py filings
   ```

9. Start the PSC worker in a second terminal:

   ```bash
   python worker.py psc
   ```

10. Start the dashboard:

   ```bash
   streamlit run app.py
   ```

11. Optionally start the PSC-statements worker in a third terminal:

   ```bash
   python worker.py psc_statements
   ```

## GitHub deployment

1. Create a new GitHub repository.
2. Add all files except `.env` and `.streamlit/secrets.toml`.
3. Commit and push:

   ```bash
   git init
   git add .
   git commit -m "Initial Companies House monitor"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
   git push -u origin main
   ```

## Streamlit Community Cloud

1. Go to Streamlit Community Cloud.
2. Choose **Create app**.
3. Select the GitHub repository, branch `main`, and file `app.py`.
4. Open **Advanced settings**.
5. Add the secrets below, replacing the values:

   ```toml
   COMPANIES_HOUSE_REST_API_KEY = "..."
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_KEY = "..."
   ```

6. Deploy.

The dashboard can be hosted on Streamlit Community Cloud, but the streaming workers should initially run on your own computer. Community Cloud is designed to deploy the dashboard from GitHub and supports secrets through the deployment settings. [web:71][web:76]

## Free operating model

- Supabase free project for database storage.
- Streamlit Community Cloud for the dashboard.
- Local Python processes for the continuous stream workers.
- GitHub for source control.

The stream stops when the local computer sleeps or shuts down. Once the MVP proves useful, move the worker to an always-on host.

## Troubleshooting

- HTTP 401: check the correct Companies House REST or stream key.
- HTTP 416: the saved stream timepoint may no longer be available; temporarily set `STREAM_START_TIMEPOINT=0` and clear the relevant row in `stream_checkpoints`.
- No dashboard data: confirm that `worker.py` is running and writing to Supabase.
- Duplicate rows: verify the database schema was run and the unique constraints exist.
- Empty PSC names: inspect the raw PSC payload because legal-entity and individual records can have different fields.
