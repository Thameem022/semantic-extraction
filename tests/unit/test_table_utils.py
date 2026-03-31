"""Tests for shared.table_utils.flatten_tables_to_markdown."""

from shared.table_utils import flatten_tables_to_markdown


def _cell(
    r: int,
    c: int,
    content: str,
    *,
    page: int | None = None,
    bounding_regions: list | None = None,
) -> dict:
    d: dict = {"rowIndex": r, "columnIndex": c, "content": content}
    if bounding_regions is not None:
        d["boundingRegions"] = bounding_regions
    elif page is not None:
        d["boundingRegions"] = [{"pageNumber": page, "polygon": []}]
    return d


class TestFlattenTablesToMarkdown:
    def test_missing_or_empty_document_tables(self):
        assert flatten_tables_to_markdown({}) == ""
        assert flatten_tables_to_markdown({"documentTables": None}) == ""
        assert flatten_tables_to_markdown({"documentTables": []}) == ""

    def test_document_tables_not_list(self):
        assert flatten_tables_to_markdown({"documentTables": "bad"}) == ""

    def test_skips_too_small_tables(self):
        layout = {
            "documentTables": [
                {
                    "rowCount": 1,
                    "columnCount": 2,
                    "cells": [_cell(0, 0, "A", page=1), _cell(0, 1, "B", page=1)],
                },
                {
                    "rowCount": 2,
                    "columnCount": 0,
                    "cells": [_cell(0, 0, "A", page=1), _cell(1, 0, "B", page=1)],
                },
            ]
        }
        assert flatten_tables_to_markdown(layout) == ""

    def test_skips_empty_cells(self):
        layout = {
            "documentTables": [
                {"rowCount": 2, "columnCount": 2, "cells": []},
            ]
        }
        assert flatten_tables_to_markdown(layout) == ""

    def test_basic_markdown_and_separator(self):
        layout = {
            "documentTables": [
                {
                    "rowCount": 2,
                    "columnCount": 2,
                    "cells": [
                        _cell(0, 0, "H1", page=1),
                        _cell(0, 1, "H2", page=1),
                        _cell(1, 0, "a", page=1),
                        _cell(1, 1, "b", page=1),
                    ],
                }
            ]
        }
        out = flatten_tables_to_markdown(layout)
        assert "## Table 1 (Page 1)" in out
        assert "| H1 | H2 |" in out
        assert "| --- | --- |" in out
        assert "| a | b |" in out

    def test_newline_hygiene_in_cells(self):
        layout = {
            "documentTables": [
                {
                    "rowCount": 2,
                    "columnCount": 1,
                    "cells": [
                        _cell(0, 0, "Line1\nLine2", page=1),
                        _cell(1, 0, "x\r\ny", page=1),
                    ],
                }
            ]
        }
        out = flatten_tables_to_markdown(layout)
        assert "Line1 Line2" in out
        assert "x y" in out
        assert "\n\n" not in out.split("| Line1 Line2 |")[0]  # no raw multiline in cell segment

    def test_page_filter_excludes_late_pages(self):
        layout = {
            "documentTables": [
                {
                    "rowCount": 2,
                    "columnCount": 1,
                    "cells": [
                        _cell(0, 0, "a", page=10),
                        _cell(1, 0, "b", page=10),
                    ],
                }
            ]
        }
        assert flatten_tables_to_markdown(layout, max_pages=5) == ""

    def test_normalized_cell_without_bounding_regions_uses_page_one(self):
        layout = {
            "documentTables": [
                {
                    "rowCount": 2,
                    "columnCount": 1,
                    "cells": [
                        {"rowIndex": 0, "columnIndex": 0, "content": "h", "boundingBox": [0] * 8},
                        {"rowIndex": 1, "columnIndex": 0, "content": "v", "boundingBox": [0] * 8},
                    ],
                }
            ]
        }
        out = flatten_tables_to_markdown(layout, max_pages=5)
        assert "Page 1" in out

    def test_table_index_only_counts_included_tables(self):
        layout = {
            "documentTables": [
                {
                    "rowCount": 2,
                    "columnCount": 1,
                    "cells": [_cell(0, 0, "skip", page=99), _cell(1, 0, "x", page=99)],
                },
                {
                    "rowCount": 2,
                    "columnCount": 1,
                    "cells": [_cell(0, 0, "h", page=1), _cell(1, 0, "v", page=1)],
                },
            ]
        }
        out = flatten_tables_to_markdown(layout, max_pages=5)
        assert "## Table 1 (Page 1)" in out
        assert "Table 2" not in out

    def test_out_of_bounds_cell_ignored(self):
        layout = {
            "documentTables": [
                {
                    "rowCount": 2,
                    "columnCount": 1,
                    "cells": [
                        _cell(0, 0, "h", page=1),
                        _cell(1, 0, "v", page=1),
                        _cell(2, 0, "bad", page=1),
                    ],
                }
            ]
        }
        out = flatten_tables_to_markdown(layout)
        assert "bad" not in out
