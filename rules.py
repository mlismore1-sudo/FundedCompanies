from datetime import date, datetime, timedelta


def parse_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(str(value)[:10]).date()


def is_sh01(item: dict) -> bool:
    return (item.get("type") or "").upper() == "SH01"


def classify(has_sh01: bool, has_new_psc: bool, has_new_rle: bool, has_statement: bool):
    if has_sh01 and (has_new_psc or has_new_rle):
        return "SH01 + new PSC/RLE", 90
    if has_sh01:
        return "SH01 only", 55
    if has_new_psc or has_new_rle:
        return "New PSC/RLE only", 50
    if has_statement:
        return "PSC statement change", 25
    return "Other", 0


def explanation(has_sh01, has_new_psc, has_new_rle, has_statement):
    parts = []
    if has_sh01:
        parts.append("SH01 detected")
    if has_new_psc:
        parts.append("new individual PSC detected")
    if has_new_rle:
        parts.append("new RLE detected")
    if has_statement:
        parts.append("PSC statement detected")
    return "; ".join(parts)
