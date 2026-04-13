"""Tests for candidate orchestration deduplication behavior.

The deduplication logic (_deduplicate_candidates, _overlap_score, etc.)
was removed when fn_build_candidates was refactored to use
StructuredIngestionPackage from 3 LLM calls instead of list[Candidate].

These tests are retained as stubs; the corresponding coverage now lives
in test_candidate_builder_waterfall.py.
"""
