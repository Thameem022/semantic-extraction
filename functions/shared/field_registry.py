"""Canonical field definitions and shared field value normalization."""

from __future__ import annotations

import re
from datetime import datetime

DATE_PATTERN = r"\d{1,2}/\d{1,2}/\d{4}"
CURRENCY_PATTERN = r"\$?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?"

# KV-only applicant fields (aliases used by CandidateBuilder; exact match after normalization).
APPLICANT_KV_FIELD_IDS: frozenset[str] = frozenset(
    {
        "applicant_name",
        "insured_address",
        "naics_code",
        "sic_naics_code",
        "year_established",
        "telephone_number",
        "website",
        "business_description",
        "emp_full_time",
        "email_address",
    }
)

# Applicant KV pairs are only accepted from these pages (avoids footer / agency blocks on later pages).
APPLICANT_KV_ALLOWED_PAGES: frozenset[int] = frozenset((1, 2))


def normalize_kv_key_label(text: str) -> str:
    """Normalize a form label for strict, deterministic registry lookup (exact equality).

    Steps: collapse whitespace; remove parenthetical segments (``(...)``); strip leading
    list markers (digit-dot or single-char-dot, e.g. ``1. ``, ``a.``); lowercase; remove
    apostrophes; strip trailing colons, asterisks, and other trailing punctuation/whitespace.
    """
    s = str(text).strip()
    s = re.sub(r"\s+", " ", s)
    while True:
        t = re.sub(r"\([^()]*\)", "", s)
        if t == s:
            break
        s = t.strip()
    s = re.sub(r"\s+", " ", s)
    while True:
        t = re.sub(r"^(?:\d+\.|\w\.)\s*", "", s, flags=re.IGNORECASE)
        if t == s:
            break
        s = t.strip()
    s = s.lower()
    s = s.replace("'", "")
    s = re.sub(r"\s+", " ", s)
    while len(s) > 0 and s[-1] in ":;*., ":
        s = s[:-1].rstrip()
    return s.strip()


CANONICAL_FIELD_REGISTRY: dict[str, dict[str, object]] = {
    "policy_number": {
        "aliases": ["Policy No", "Account Number", "Policy #"],
    },
    "effective_date": {
        "aliases": ["Proposed Effective Date"],
        "regex": DATE_PATTERN,
    },
    "limit_employment_practices": {
        "aliases": ["Employment Practices"],
        "columnHeader": "Limit",
        "regex": CURRENCY_PATTERN,
    },
    "retention_employment_practices": {
        "aliases": ["Employment Practices"],
        "columnHeader": "Retention",
        "regex": CURRENCY_PATTERN,
    },
    # Applicant Info (KV extraction)
    "applicant_name": {
        "aliases": [
            "Name of Applicant:",
            "Name of Applicant",
            "Applicant Name:",
            "Name of Insured:",
            "Entity Name:",
            "Primary Applicant's name:",
            "Primary Applicant's name",
        ],
    },
    "insured_address": {
        "aliases": [
            "Street Address:",
            "Address of Applicant*",
            "Address of Applicant",
            "Address:",
            "City, State, ZIP Code:",
            "City State ZIP Code:",
            "Location address",
            "Location address:",
        ],
    },
    "naics_code": {
        "aliases": [
            "NAICS Code:",
            "Primary SIC Code:",
        ],
    },
    "sic_naics_code": {
        "aliases": [
            "SIC/NAICS Code:",
            "Primary SIC/NAICS Code:",
            "SIC Code:",
        ],
    },
    "year_established": {
        "aliases": [
            "Year Established:",
            "Year Applicant's business was established:",
            "Years of Operation:",
        ],
    },
    "telephone_number": {
        "aliases": [
            "Telephone Number:",
            "Phone Number:",
            "Telephone Number",
            "Phone Number",
            "Telephone",
            "Business Phone:",
        ],
    },
    "website": {
        "aliases": [
            "Website Address:",
            "Website:",
            "Company Website:",
            "Web Site:",
            "Applicant's Web Site",
            "Web address",
            "Web address:",
        ],
    },
    "emp_full_time": {
        "aliases": [
            "Total worldwide employees",
            "Total worldwide employees:",
        ],
    },
    "email_address": {
        "aliases": [
            "e-Mail",
            "e-Mail:",
            "E-mail:",
            "Email:",
        ],
    },
    "business_description": {
        "aliases": [
            "Description of Applicant's operations:",
            "Description of Applicant's operations",
            "Description of Operations:",
            "Nature of Business:",
            "Business Description:",
        ],
    },
}


def _combined_insured_address_norms() -> frozenset[str]:
    """Normalized forms for combined city/state/ZIP KV keys (must match `insured_address` aliases)."""
    combined_aliases = [
        "City, State, ZIP Code:",
        "City State ZIP Code:",
    ]
    return frozenset(normalize_kv_key_label(a) for a in combined_aliases)


COMBINED_INSURED_ADDRESS_LABEL_NORMS: frozenset[str] = _combined_insured_address_norms()


def normalize_value(text: str, field_type: str) -> str:
    """Normalize date and currency values into deterministic formats."""
    value = (text or "").strip()
    normalized_type = (field_type or "").strip().lower()

    if not value:
        return value

    if "date" in normalized_type:
        if re.fullmatch(DATE_PATTERN, value):
            parsed = datetime.strptime(value, "%m/%d/%Y")
            return parsed.strftime("%Y-%m-%d")
        return value

    if any(token in normalized_type for token in ("limit", "retention", "currency", "amount")):
        return value.replace("$", "").replace(",", "").replace(" ", "")

    return value
