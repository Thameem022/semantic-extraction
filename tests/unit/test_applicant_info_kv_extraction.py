import pytest

from shared import CandidateBuilder


def _poly():
    return [0.0, 0.0, 10.0, 0.0, 10.0, 10.0, 0.0, 10.0]


def _kv_pair(*, key: str, value: str, page_number: int = 1) -> dict:
    return {
        "key": {"content": key},
        "value": {
            "content": value,
            "boundingRegions": [{"pageNumber": page_number, "polygon": _poly()}],
        },
    }


def test_applicant_name_matches_registry_after_list_prefix_and_parens_removed():
    good = CandidateBuilder(
        {
            "pages": [],
            "keyValuePairs": [
                _kv_pair(key="1. Name of Applicant (See #4):", value="JOHN DOE"),
            ],
        }
    ).kv_hunter()
    assert len(good) == 1
    assert good[0].fieldId == "applicant_name"
    assert good[0].rawValue == "JOHN DOE"


def test_applicant_name_case_insensitive_and_min_length():
    good = CandidateBuilder(
        {
            "pages": [],
            "keyValuePairs": [
                _kv_pair(key="NAME OF APPLICANT:", value="JOHN DOE"),
            ],
        }
    ).kv_hunter()

    assert len(good) == 1
    assert good[0].fieldId == "applicant_name"
    assert good[0].rawValue == "JOHN DOE"
    assert good[0].confidence == 0.95
    assert good[0].source == "KV"
    assert good[0].contextChunk == "NAME OF APPLICANT: JOHN DOE"

    bad = CandidateBuilder(
        {
            "pages": [],
            "keyValuePairs": [
                _kv_pair(key="Name of Applicant:", value="AB"),
            ],
        }
    ).kv_hunter()
    assert bad == []


@pytest.mark.parametrize(
    "kv_value,expected",
    [
        ("1977", "1977"),
        ("Year: 1977", "1977"),
    ],
)
def test_year_established_accepts_four_digit_year(kv_value: str, expected: str):
    candidates = CandidateBuilder(
        {
            "pages": [],
            "keyValuePairs": [
                _kv_pair(key="Years of Operation:", value=kv_value),
            ],
        }
    ).kv_hunter()

    assert len(candidates) == 1
    assert candidates[0].fieldId == "year_established"
    assert candidates[0].rawValue == expected
    assert candidates[0].contextChunk == f"Years of Operation: {expected}"


@pytest.mark.parametrize("kv_value", ["02", "01", "202", "abc", ""])
def test_year_established_rejects_fragments(kv_value: str):
    candidates = CandidateBuilder(
        {
            "pages": [],
            "keyValuePairs": [
                _kv_pair(key="Year Established:", value=kv_value),
            ],
        }
    ).kv_hunter()
    assert candidates == []


def test_insured_address_concatenates_applicant_city_state_zip_and_avoids_agent_city():
    layout = {
        "pages": [],
        "keyValuePairs": [
            _kv_pair(key="Street Address:", value="123 MAIN ST"),
            _kv_pair(key="Applicant City:", value="TAMPA"),
            _kv_pair(key="Agent City:", value="ORLANDO"),
            _kv_pair(key="Applicant State:", value="FL"),
            _kv_pair(key="Applicant Zip Code:", value="33601"),
        ],
    }

    candidates = CandidateBuilder(layout).kv_hunter()
    assert len(candidates) == 1
    c = candidates[0]
    assert c.fieldId == "insured_address"
    assert c.rawValue == "123 MAIN ST, TAMPA, FL, 33601"
    assert c.contextChunk == "Street Address: 123 MAIN ST, TAMPA, FL, 33601"


def test_insured_address_generic_city_state_zip_code_on_page_one_travelers_like():
    layout = {
        "pages": [],
        "keyValuePairs": [
            _kv_pair(key="Street Address:", value="123 MAIN ST", page_number=1),
            _kv_pair(key="City:", value="BIRMINGHAM", page_number=1),
            _kv_pair(key="State:", value="AL", page_number=1),
            _kv_pair(key="ZIP Code:", value="35216", page_number=1),
        ],
    }
    candidates = CandidateBuilder(layout).kv_hunter()
    assert len(candidates) == 1
    c = candidates[0]
    assert c.fieldId == "insured_address"
    assert c.rawValue == "123 MAIN ST, BIRMINGHAM, AL, 35216"
    assert c.contextChunk == "Street Address: 123 MAIN ST, BIRMINGHAM, AL, 35216"


def test_insured_address_generic_city_state_zip_on_page_two_concatenates():
    layout = {
        "pages": [],
        "keyValuePairs": [
            _kv_pair(key="Street Address:", value="123 MAIN ST", page_number=1),
            _kv_pair(key="City:", value="TAMPA", page_number=2),
            _kv_pair(key="State:", value="FL", page_number=2),
            _kv_pair(key="Zip:", value="33601", page_number=2),
        ],
    }
    candidates = CandidateBuilder(layout).kv_hunter()
    assert len(candidates) == 1
    assert candidates[0].rawValue == "123 MAIN ST, TAMPA, FL, 33601"


def test_insured_address_generic_components_on_page_three_not_concatenated():
    layout = {
        "pages": [],
        "keyValuePairs": [
            _kv_pair(key="Street Address:", value="123 MAIN ST", page_number=1),
            _kv_pair(key="City:", value="WRONG", page_number=3),
            _kv_pair(key="State:", value="XX", page_number=3),
            _kv_pair(key="Zip:", value="99999", page_number=3),
        ],
    }
    candidates = CandidateBuilder(layout).kv_hunter()
    assert len(candidates) == 1
    assert candidates[0].rawValue == "123 MAIN ST"


def test_insured_address_agency_city_excluded_prefers_generic_applicant_city():
    layout = {
        "pages": [],
        "keyValuePairs": [
            _kv_pair(key="Street Address:", value="123 MAIN ST", page_number=1),
            _kv_pair(key="City:", value="BIRMINGHAM", page_number=1),
            _kv_pair(key="Agency City:", value="ORLANDO", page_number=1),
            _kv_pair(key="State:", value="AL", page_number=1),
            _kv_pair(key="Zip:", value="35216", page_number=1),
        ],
    }
    candidates = CandidateBuilder(layout).kv_hunter()
    assert len(candidates) == 1
    assert candidates[0].rawValue == "123 MAIN ST, BIRMINGHAM, AL, 35216"


def test_insured_address_combined_city_state_zip_code_uses_full_value_page_one():
    layout = {
        "pages": [],
        "keyValuePairs": [
            _kv_pair(
                key="City, State, ZIP Code:",
                value="NORTH VERNON, IN 47265",
                page_number=1,
            ),
        ],
    }
    candidates = CandidateBuilder(layout).kv_hunter()
    assert len(candidates) == 1
    c = candidates[0]
    assert c.fieldId == "insured_address"
    assert c.rawValue == "NORTH VERNON, IN 47265"
    assert c.contextChunk == "City, State, ZIP Code: NORTH VERNON, IN 47265"


def test_insured_address_combined_city_state_zip_accepted_on_page_two():
    layout = {
        "pages": [],
        "keyValuePairs": [
            _kv_pair(
                key="City, State, ZIP Code:",
                value="ORLANDO, FL 32801",
                page_number=2,
            ),
        ],
    }
    candidates = CandidateBuilder(layout).kv_hunter()
    assert len(candidates) == 1
    assert candidates[0].rawValue == "ORLANDO, FL 32801"


def test_insured_address_combined_skipped_on_page_three():
    layout = {
        "pages": [],
        "keyValuePairs": [
            _kv_pair(
                key="City, State, ZIP Code:",
                value="ORLANDO, FL 32801",
                page_number=3,
            ),
        ],
    }
    assert CandidateBuilder(layout).kv_hunter() == []


def test_page_one_only_fields_ignored_on_later_pages():
    layout = {
        "pages": [],
        "keyValuePairs": [
            _kv_pair(key="Telephone Number:", value="555-000-1111", page_number=1),
            _kv_pair(key="Website Address:", value="https://insured.example.com", page_number=1),
            _kv_pair(key="Description of Applicant's operations:", value="Widget manufacturing", page_number=1),
            _kv_pair(key="SIC/NAICS Code:", value="12345", page_number=1),
            _kv_pair(key="Telephone Number:", value="555-999-8888", page_number=3),
            _kv_pair(key="Website:", value="https://agency.example.com", page_number=3),
        ],
    }
    candidates = CandidateBuilder(layout).kv_hunter()
    by_id = {c.fieldId: c for c in candidates}
    assert by_id["telephone_number"].rawValue == "5550001111"
    assert by_id["website"].rawValue == "https://insured.example.com"
    assert by_id["business_description"].rawValue == "Widget manufacturing"
    assert by_id["sic_naics_code"].rawValue == "12345"
    assert sum(1 for c in candidates if c.fieldId == "telephone_number") == 1
    assert sum(1 for c in candidates if c.fieldId == "website") == 1


def test_telephone_parentheses_format_normalized_to_ten_digits():
    layout = {
        "pages": [],
        "keyValuePairs": [
            _kv_pair(key="Telephone Number:", value="(555) 000-1111", page_number=1),
        ],
    }
    c = CandidateBuilder(layout).kv_hunter()[0]
    assert c.rawValue == "5550001111"


def test_sic_naics_code_extracts_digits_from_prose_multiline():
    layout = {
        "pages": [],
        "keyValuePairs": [
            _kv_pair(
                key="SIC Code:",
                value="NEW CAR SALES/SERVICE\n5511",
                page_number=1,
            ),
        ],
    }
    candidates = CandidateBuilder(layout).kv_hunter()
    assert len(candidates) == 1
    assert candidates[0].fieldId == "sic_naics_code"
    assert candidates[0].rawValue == "5511"
    assert candidates[0].contextChunk == "SIC Code: 5511"


def test_primary_applicant_name_matches_serenity_caregivers_value():
    candidates = CandidateBuilder(
        {
            "pages": [],
            "keyValuePairs": [
                _kv_pair(
                    key="1. Primary Applicant's name (See #4):",
                    value="Serenity Caregivers LLC.",
                ),
            ],
        }
    ).kv_hunter()
    assert len(candidates) == 1
    assert candidates[0].fieldId == "applicant_name"
    assert candidates[0].rawValue == "Serenity Caregivers LLC."


def test_primary_applicant_name_without_trailing_colon_serenity_layout():
    candidates = CandidateBuilder(
        {
            "pages": [],
            "keyValuePairs": [
                _kv_pair(
                    key="Primary Applicant's name (See #4)",
                    value="Serenity Caregivers LLC.",
                    page_number=2,
                ),
            ],
        }
    ).kv_hunter()
    assert len(candidates) == 1
    assert candidates[0].fieldId == "applicant_name"
    assert candidates[0].rawValue == "Serenity Caregivers LLC."


def test_location_address_alias_insured_address():
    candidates = CandidateBuilder(
        {
            "pages": [],
            "keyValuePairs": [
                _kv_pair(key="Location address:", value="100 Main Street", page_number=1),
            ],
        }
    ).kv_hunter()
    assert len(candidates) == 1
    assert candidates[0].fieldId == "insured_address"
    assert "100 Main Street" in candidates[0].rawValue


def test_web_address_alias_on_page_two():
    candidates = CandidateBuilder(
        {
            "pages": [],
            "keyValuePairs": [
                _kv_pair(key="Web address", value="https://insured.example.org", page_number=2),
            ],
        }
    ).kv_hunter()
    assert len(candidates) == 1
    assert candidates[0].fieldId == "website"
    assert candidates[0].rawValue == "https://insured.example.org"


def test_year_established_numbered_label_maps_2024():
    candidates = CandidateBuilder(
        {
            "pages": [],
            "keyValuePairs": [
                _kv_pair(key="1. Year established", value="2024"),
            ],
        }
    ).kv_hunter()
    assert len(candidates) == 1
    assert candidates[0].fieldId == "year_established"
    assert candidates[0].rawValue == "2024"


def test_sic_naics_code_returns_first_four_five_or_six_digit_run():
    layout = {
        "pages": [],
        "keyValuePairs": [
            _kv_pair(key="SIC/NAICS Code:", value="Line 5511 and NAICS 441110", page_number=1),
        ],
    }
    c = CandidateBuilder(layout).kv_hunter()[0]
    assert c.rawValue == "5511"


def test_sic_naics_code_first_run_wins_over_later_longer_code():
    layout = {
        "pages": [],
        "keyValuePairs": [
            _kv_pair(key="SIC/NAICS Code:", value="5511 44111", page_number=1),
        ],
    }
    c = CandidateBuilder(layout).kv_hunter()[0]
    assert c.rawValue == "5511"


def test_business_description_emits_sic_naics_when_digits_in_value():
    layout = {
        "pages": [],
        "keyValuePairs": [
            _kv_pair(
                key="Description of Applicant's operations:",
                value="Retail auto parts (NAICS 441110) and service",
                page_number=1,
            ),
        ],
    }
    candidates = CandidateBuilder(layout).kv_hunter()
    assert len(candidates) == 2
    desc = next(c for c in candidates if c.fieldId == "business_description")
    sic = next(c for c in candidates if c.fieldId == "sic_naics_code")
    assert "Retail auto parts" in desc.rawValue
    assert sic.rawValue == "441110"
    assert sic.contextChunk.startswith("Description of Applicant's operations:")


def test_street_and_combined_insured_address_both_emit_candidates():
    layout = {
        "pages": [],
        "keyValuePairs": [
            _kv_pair(key="Street Address:", value="100 INDUSTRIAL RD", page_number=1),
            _kv_pair(key="City, State, ZIP Code:", value="NORTH VERNON, IN 47265", page_number=1),
        ],
    }
    candidates = CandidateBuilder(layout).kv_hunter()
    assert len(candidates) == 2
    assert {c.rawValue for c in candidates} == {"100 INDUSTRIAL RD", "NORTH VERNON, IN 47265"}


def test_telephone_extracts_digits_from_parentheses_format():
    c = CandidateBuilder(
        {
            "pages": [],
            "keyValuePairs": [
                _kv_pair(key="Telephone", value="(215) 475-1400", page_number=1),
            ],
        }
    ).kv_hunter()[0]
    assert c.fieldId == "telephone_number"
    assert c.rawValue == "2154751400"


def test_is_partners_style_layout():
    layout = {
        "pages": [],
        "keyValuePairs": [
            _kv_pair(key="1. Name of Applicant", value="IS Partners LLC.", page_number=1),
            _kv_pair(key="Address of Applicant", value="123 Market St, Philadelphia, PA", page_number=1),
            _kv_pair(key="Telephone", value="(215) 475-1400", page_number=1),
            _kv_pair(key="Applicant's Web Site", value="https://www.ispartners.example.com", page_number=1),
            _kv_pair(key="e-Mail", value="contact@ispartners.example.com", page_number=1),
            _kv_pair(key="Total worldwide employees", value="46", page_number=1),
        ],
    }
    candidates = CandidateBuilder(layout).kv_hunter()
    by_id = {c.fieldId: c for c in candidates}
    assert by_id["applicant_name"].rawValue == "IS Partners LLC."
    assert by_id["insured_address"].rawValue == "123 Market St, Philadelphia, PA"
    assert by_id["telephone_number"].rawValue == "2154751400"
    assert by_id["website"].rawValue == "https://www.ispartners.example.com"
    assert by_id["email_address"].rawValue == "contact@ispartners.example.com"
    assert by_id["emp_full_time"].rawValue == "46"

