"""Tests for candidate orchestration deduplication behavior."""

from shared.models.candidate import Candidate

from fn_build_candidates import _deduplicate_candidates


def _candidate(
    *,
    field_id: str,
    source: str,
    raw_value: str,
    confidence: float = 0.5,
    page_number: int = 1,
    bounding_box: list[float] | None = None,
) -> Candidate:
    return Candidate(
        fieldId=field_id,
        rawValue=raw_value,
        normalizedValue=raw_value,
        confidence=confidence,
        source=source,
        pageNumber=page_number,
        boundingBox=bounding_box or [0.0, 0.0, 10.0, 0.0, 10.0, 10.0, 0.0, 10.0],
        contextChunk="context",
    )


def test_deduplicate_prefers_higher_priority_source_and_merges_sources():
    pattern = _candidate(
        field_id="policy_number",
        source="Pattern",
        raw_value="PN-OLD",
        confidence=0.7,
    )
    kv = _candidate(
        field_id="policy_number",
        source="KV",
        raw_value="PN-NEW",
        confidence=0.5,
        bounding_box=[1.0, 1.0, 9.0, 1.0, 9.0, 9.0, 1.0, 9.0],
    )

    deduped = _deduplicate_candidates([pattern, kv])

    assert len(deduped) == 1
    assert deduped[0].rawValue == "PN-NEW"
    assert deduped[0].source == "KV | Pattern"


def test_deduplicate_keeps_non_overlapping_candidates():
    first = _candidate(
        field_id="policy_number",
        source="KV",
        raw_value="PN-1",
        bounding_box=[0.0, 0.0, 10.0, 0.0, 10.0, 10.0, 0.0, 10.0],
    )
    second = _candidate(
        field_id="policy_number",
        source="Table",
        raw_value="PN-2",
        bounding_box=[20.0, 20.0, 30.0, 20.0, 30.0, 30.0, 20.0, 30.0],
    )

    deduped = _deduplicate_candidates([first, second])
    assert len(deduped) == 2


def test_deduplicate_does_not_merge_different_pages():
    page_one = _candidate(
        field_id="policy_number",
        source="KV",
        raw_value="PN-1",
        page_number=1,
    )
    page_two = _candidate(
        field_id="policy_number",
        source="Pattern",
        raw_value="PN-2",
        page_number=2,
    )

    deduped = _deduplicate_candidates([page_one, page_two])
    assert len(deduped) == 2
