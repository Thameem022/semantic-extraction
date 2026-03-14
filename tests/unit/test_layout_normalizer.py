"""Tests for shared.layout_normalizer.normalize_layout_result."""

import pytest

from shared.layout_normalizer import normalize_layout_result


class TestNormalizeLayoutResult:
    def test_empty_result_returns_doc_id_and_empty_pages(self):
        out = normalize_layout_result("doc-1", "prebuilt-layout", {})
        assert out["docId"] == "doc-1"
        assert out["modelId"] == "prebuilt-layout"
        assert out["pages"] == []

    def test_analyze_result_key_used(self):
        result = {"analyzeResult": {"pages": []}}
        out = normalize_layout_result("d1", None, result)
        assert out["docId"] == "d1"
        assert out["modelId"] is None
        assert out["pages"] == []

    def test_single_page_with_lines_normalized(self):
        result = {
            "analyzeResult": {
                "pages": [
                    {
                        "pageNumber": 1,
                        "width": 8.5,
                        "height": 11.0,
                        "unit": "inch",
                        "lines": [
                            {"content": "Hello", "boundingBox": [0.0, 0.0, 1.0, 0.2], "spans": []},
                        ],
                        "words": [],
                        "tables": [],
                    }
                ]
            }
        }
        out = normalize_layout_result("doc-2", "prebuilt-layout", result)
        assert len(out["pages"]) == 1
        page = out["pages"][0]
        assert page["pageNumber"] == 1
        assert page["width"] == 8.5
        assert page["height"] == 11.0
        assert page["unit"] == "inch"
        assert len(page["lines"]) == 1
        assert page["lines"][0]["content"] == "Hello"
        assert page["lines"][0]["boundingBox"] == [0.0, 0.0, 1.0, 0.2]

    def test_non_dict_result_treated_as_empty(self):
        out = normalize_layout_result("d3", None, None)
        assert out["docId"] == "d3"
        assert out["pages"] == []

    def test_key_value_pairs_empty_list(self):
        result = {"analyzeResult": {"pages": [], "keyValuePairs": []}}
        out = normalize_layout_result("doc-kv", "prebuilt-layout", result)
        assert "keyValuePairs" in out
        assert out["keyValuePairs"] == []

    def test_key_value_pairs_missing_returns_empty_list(self):
        result = {"analyzeResult": {"pages": []}}
        out = normalize_layout_result("doc-kv2", None, result)
        assert "keyValuePairs" in out
        assert out["keyValuePairs"] == []

    def test_key_value_pairs_normalized(self):
        result = {
            "analyzeResult": {
                "pages": [],
                "keyValuePairs": [
                    {
                        "key": {
                            "content": "Policy Number",
                            "spans": [{"offset": 0, "length": 14}],
                            "boundingRegions": [
                                {"pageNumber": 1, "polygon": [1.0, 2.0, 3.0, 2.0, 3.0, 3.0, 1.0, 3.0]},
                            ],
                        },
                        "value": {
                            "content": "P-12345",
                            "spans": [{"offset": 15, "length": 7}],
                        },
                    },
                ],
            }
        }
        out = normalize_layout_result("doc-kv3", "prebuilt-layout", result)
        assert len(out["keyValuePairs"]) == 1
        pair = out["keyValuePairs"][0]
        assert pair["key"]["content"] == "Policy Number"
        assert pair["key"]["spans"] == [{"offset": 0, "length": 14, "confidence": None}]
        assert pair["key"]["boundingRegions"] == [
            {"pageNumber": 1, "polygon": [1.0, 2.0, 3.0, 2.0, 3.0, 3.0, 1.0, 3.0]},
        ]
        assert pair["value"]["content"] == "P-12345"
        assert pair["value"]["spans"] == [{"offset": 15, "length": 7, "confidence": None}]
        assert pair["value"]["boundingRegions"] is None
