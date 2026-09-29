import base64
import json
import os
from typing import Any, Dict, Iterator, Optional

import requests

REST_BASE = "https://api.company-information.service.gov.uk"
STREAM_BASE = "https://stream.companieshouse.gov.uk"


def _key(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


def _basic_auth(key: str) -> str:
    token = base64.b64encode(f"{key}:".encode()).decode()
    return f"Basic {token}"


def rest_get(path: str, params: Optional[dict] = None) -> Dict[str, Any]:
    response = requests.get(
        f"{REST_BASE}{path}",
        headers={"Authorization": _basic_auth(_key("COMPANIES_HOUSE_REST_API_KEY"))},
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def company_profile(company_number: str) -> Dict[str, Any]:
    return rest_get(f"/company/{company_number}")


def filing_history(company_number: str, items_per_page: int = 100) -> Dict[str, Any]:
    return rest_get(
        f"/company/{company_number}/filing-history",
        params={"items_per_page": items_per_page},
    )


def psc_list(company_number: str, items_per_page: int = 100) -> Dict[str, Any]:
    return rest_get(
        f"/company/{company_number}/persons-with-significant-control",
        params={"items_per_page": items_per_page},
    )


def stream_events(endpoint: str, timepoint: int = 0, timeout: int = 60) -> Iterator[dict]:
    headers = {
        "Authorization": _basic_auth(_key("COMPANIES_HOUSE_STREAM_API_KEY")),
        "Accept": "application/json",
    }
    with requests.get(
        f"{STREAM_BASE}{endpoint}",
        headers=headers,
        params={"timepoint": timepoint},
        stream=True,
        timeout=(30, timeout),
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            if line.startswith("data:"):
                line = line[5:].strip()
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue
