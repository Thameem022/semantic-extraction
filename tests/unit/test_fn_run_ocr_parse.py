"""Tests for fn_run_ocr._parse_raw_blob_name and related helpers."""

import asyncio

import pytest

from fn_run_ocr import _get_document_and_partition_key_async, _parse_raw_blob_name


class TestParseRawBlobName:
    def test_valid_three_segments_legacy_raw(self):
        doc_id, filename, policy_type = _parse_raw_blob_name("raw/abc-123/doc.pdf")
        assert doc_id == "abc-123"
        assert filename == "doc.pdf"
        assert policy_type is None

    def test_valid_uuid_like_doc_id_legacy_raw(self):
        doc_id, filename, policy_type = _parse_raw_blob_name(
            "raw/550e8400-e29b-41d4-a716-446655440000/sample.pdf"
        )
        assert doc_id == "550e8400-e29b-41d4-a716-446655440000"
        assert filename == "sample.pdf"
        assert policy_type is None

    def test_filename_with_slash_in_path_treated_as_single_name_legacy_raw(self):
        doc_id, filename, policy_type = _parse_raw_blob_name("raw/doc1/folder/file.pdf")
        assert doc_id == "doc1"
        assert filename == "folder/file.pdf"
        assert policy_type is None

    def test_new_style_raw_with_policy_type(self):
        doc_id, filename, policy_type = _parse_raw_blob_name(
            "raw/home-auto/abcd-uuid/file.pdf"
        )
        assert doc_id == "abcd-uuid"
        assert filename == "file.pdf"
        assert policy_type == "home-auto"

    def test_incoming_test_path_uses_filename_stem_as_doc_id(self):
        doc_id, filename, policy_type = _parse_raw_blob_name(
            "incoming/test/sample-document.pdf"
        )
        assert doc_id == "sample-document"
        assert filename == "sample-document.pdf"
        assert policy_type is None

    def test_empty_blob_name_raises(self):
        with pytest.raises(ValueError, match="Blob name is empty"):
            _parse_raw_blob_name("")

    def test_wrong_container_prefix_raises(self):
        with pytest.raises(
            ValueError,
            match="Expected blob path to start with 'raw/' or 'incoming/test/'",
        ):
            _parse_raw_blob_name("someother/doc1/file.pdf")

    def test_only_two_segments_raises(self):
        with pytest.raises(ValueError, match="Unexpected blob name format"):
            _parse_raw_blob_name("raw/doc1")

    def test_missing_doc_id_raises(self):
        with pytest.raises(ValueError, match="Missing docId segment"):
            _parse_raw_blob_name("raw//file.pdf")

    def test_missing_filename_raises(self):
        with pytest.raises(ValueError, match="Missing filename segment"):
            _parse_raw_blob_name("raw/doc1/")


class FakeAsyncQueryContainer:
    def __init__(self, results_for_kwargs):
        # results_for_kwargs: list of (kwargs_predicate, results_list)
        self._results_for_kwargs = results_for_kwargs

    async def query_items(self, **kwargs):
        # This is an async generator in the real SDK; emulate that here.
        for predicate, results in self._results_for_kwargs:
            if predicate(kwargs):
                for item in results:
                    yield item
                return
        # Default: no results.
        if False:
            yield None


class TestGetDocumentAndPartitionKeyAsync:
    @pytest.mark.asyncio
    async def test_partition_scoped_then_cross_partition_fallback(self):
        doc = {
            "id": "doc-1",
            "docId": "doc-1",
            "policyType": "home-auto",
            "sourceBlobPath": "raw/home-auto/doc-1/file.pdf",
        }

        def is_scoped(kwargs):
            return kwargs.get("partition_key") == "home-auto"

        def is_cross(kwargs):
            return "partition_key" not in kwargs

        container = FakeAsyncQueryContainer(
            results_for_kwargs=[
                # First call: partition-scoped returns no items.
                (is_scoped, []),
                # Fallback: cross-partition returns our document.
                (is_cross, [doc]),
            ]
        )

        found_doc, policy_type = await _get_document_and_partition_key_async(
            container,
            blob_path="raw/home-auto/doc-1/file.pdf",
            policy_type_hint="home-auto",
        )

        assert found_doc == doc
        assert policy_type == "home-auto"

    @pytest.mark.asyncio
    async def test_cross_partition_when_no_policy_type_hint(self):
        doc = {
            "id": "doc-2",
            "docId": "doc-2",
            "policyType": "auto",
            "sourceBlobPath": "raw/auto/doc-2/file.pdf",
        }

        def is_cross(kwargs):
            return "partition_key" not in kwargs

        container = FakeAsyncQueryContainer(
            results_for_kwargs=[
                (is_cross, [doc]),
            ]
        )

        found_doc, policy_type = await _get_document_and_partition_key_async(
            container,
            blob_path="raw/auto/doc-2/file.pdf",
            policy_type_hint=None,
        )

        assert found_doc == doc
        assert policy_type == "auto"
