import os
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

from ch_client import company_profile, filing_history, psc_list, stream_events
from db import (
    checkpoint,
    get_client,
    save_checkpoint,
    save_raw_event,
    upsert_company,
    upsert_filing,
    upsert_psc,
)
from rules import classify, explanation, is_sh01

load_dotenv()

STREAMS = {
    "filings": "/filings",
    "psc": "/persons-with-significant-control",
    "psc_statements": "/psc-statements",
}


def company_number_from_event(event: dict) -> str | None:
    for key in ("company_number", "companyNumber"):
        if event.get(key):
            return event[key]
    resource = event.get("resource", {})
    for key in ("company_number", "companyNumber"):
        if isinstance(resource, dict) and resource.get(key):
            return resource[key]
    return None


def process_filing_event(client, event):
    company_number = company_number_from_event(event)
    if not company_number:
        return
    profile = company_profile(company_number)
    upsert_company(client, profile)
    history = filing_history(company_number)
    sh01_items = [x for x in history.get("items", []) if is_sh01(x)]
    for item in sh01_items:
        upsert_filing(client, company_number, item)


def process_psc_event(client, event):
    company_number = company_number_from_event(event)
    if not company_number:
        return
    profile = company_profile(company_number)
    upsert_company(client, profile)
    data = psc_list(company_number)
    for item in data.get("items", []):
        upsert_psc(client, company_number, item)


def run_stream(stream_name: str, endpoint: str):
    client = get_client()
    backoff = 5
    while True:
        position = checkpoint(client, stream_name)
        try:
            for event in stream_events(endpoint, position, int(os.getenv("POLL_TIMEOUT_SECONDS", "60"))):
                meta = event.get("event", event)
                timepoint = meta.get("timepoint")
                saved = save_raw_event(client, stream_name, event)
                if saved and stream_name == "filings":
                    process_filing_event(client, event)
                elif saved and stream_name == "psc":
                    process_psc_event(client, event)
                if timepoint is not None:
                    save_checkpoint(client, stream_name, int(timepoint))
            backoff = 5
        except Exception as exc:
            print(f"{stream_name} error: {exc}", flush=True)
            time.sleep(backoff)
            backoff = min(backoff * 2, 300)


if __name__ == "__main__":
    import sys
    stream_name = sys.argv[1] if len(sys.argv) > 1 else "filings"
    if stream_name not in STREAMS:
        raise SystemExit(f"Choose one of: {', '.join(STREAMS)}")
    run_stream(stream_name, STREAMS[stream_name])
