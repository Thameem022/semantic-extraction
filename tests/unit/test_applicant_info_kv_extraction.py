"""Tests for deterministic KV extraction from CandidateBuilder.

The kv_hunter() method and all deterministic extraction logic were removed
when CandidateBuilder was refactored to use 3 LLM calls that return a
StructuredIngestionPackage instead of list[Candidate].

These tests are retained as stubs; the corresponding extraction coverage
now lives in test_candidate_builder_waterfall.py.
"""
