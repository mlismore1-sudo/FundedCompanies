import os
from datetime import datetime, timezone
from typing import Any, Optional

from supabase import Client, create_client


def get_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY are required")
    return create_client(url, key)


def checkpoint(client: Client, stream_name: str) -> int:
    result = (
        client.table("stream_checkpoints")
        .select("timepoint")
        .eq("stream_name", stream_name)
        .limit(1)
        .execute()
    )
    if result.data:
        return int(result.data[0]["timepoint"])
    return int(os.getenv("STREAM_START_TIMEPOINT", "0"))


def save_checkpoint(client: Client, stream_name: str, timepoint: int) -> None:
    client.table("stream_checkpoints").upsert(
        {
            "stream_name": stream_name,
            "timepoint": int(timepoint),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    ).execute()


def save_raw_event(client: Client, stream_name: str, event: dict) -> bool:
    meta = event.get("event", event)
    row = {
        "stream_name": stream_name,
        "company_number": event.get("company_number") or event.get("company_number", None),
        "resource_id": event.get("resource_id"),
        "event_type": meta.get("type"),
        "fields_changed": meta.get("fields_changed"),
        "published_at": meta.get("published_at"),
        "timepoint": meta.get("timepoint"),
        "raw_payload": event,
    }
    result = client.table("stream_events").upsert(
        row, on_conflict="stream_name,resource_id,timepoint"
    ).execute()
    return bool(result.data)


def upsert_company(client: Client, company: dict) -> None:
    client.table("companies").upsert(
        {
            "company_number": company.get("company_number"),
            "company_name": company.get("company_name"),
            "sic_codes": company.get("sic_codes", []),
            "date_of_incorporation": company.get("date_of_creation"),
            "company_status": company.get("company_status"),
            "profile": company,
            "last_enriched_at": datetime.now(timezone.utc).isoformat(),
        }
    ).execute()


def upsert_filing(client: Client, company_number: str, item: dict) -> None:
    client.table("filings").upsert(
        {
            "company_number": company_number,
            "transaction_id": item.get("transaction_id"),
            "form_type": item.get("type"),
            "description": item.get("description"),
            "filing_date": item.get("date"),
            "action_date": item.get("action_date"),
            "document_url": (item.get("links") or {}).get("document_metadata"),
            "raw_payload": item,
        }
    ).execute()


def upsert_psc(client: Client, company_number: str, item: dict) -> None:
    name = item.get("name") or item.get("identification", {}).get("legal_person_name")
    entity_type = item.get("kind") or item.get("identification", {}).get("legal_person_name")
    client.table("psc_records").upsert(
        {
            "company_number": company_number,
            "resource_id": item.get("etag") or item.get("links", {}).get("self"),
            "name": name,
            "entity_type": entity_type,
            "nature_of_control": item.get("natures_of_control", []),
            "notified_on": item.get("notified_on"),
            "ceased_on": item.get("ceased_on"),
            "active": not bool(item.get("ceased_on")),
            "raw_payload": item,
        }
    ).execute()


def recent_screening(client: Client, limit: int = 500) -> list[dict]:
    return (
        client.table("screening_events")
        .select("*")
        .order("detected_at", desc=True)
        .limit(limit)
        .execute()
        .data
    )
