"""Normalization helpers for Azure Document Intelligence layout results.

The goal is to provide a stable, vendor-agnostic layout schema for downstream
stages (e.g. candidate builder) so they do not depend on the SDK's object
model or wire format.

Normalized schema (layout.json)
-------------------------------
{
  "docId": "<string>",
  "modelId": "<string | null>",
  "pages": [
    {
      "pageNumber": <int>,
      "width": <float | null>,
      "height": <float | null>,
      "unit": "<string | null>",
      "lines": [
        {
          "content": "<string>",
          "boundingBox": [<float>, ...] | null,
          "spans": [
            {
              "offset": <int>,
              "length": <int>,
              "confidence": <float | null>
            }
          ] | null
        }
      ],
      "words": [
        {
          "content": "<string>",
          "boundingBox": [<float>, ...] | null,
          "confidence": <float | null>
        }
      ],
      "tables": [
        {
          "rowCount": <int>,
          "columnCount": <int>,
          "boundingBox": [<float>, ...] | null,
          "cells": [
            {
              "rowIndex": <int>,
              "columnIndex": <int>,
              "rowSpan": <int>,
              "columnSpan": <int>,
              "content": "<string>",
              "kind": "<string | null>",
              "boundingBox": [<float>, ...] | null,
              "spans": [
                {
                  "offset": <int>,
                  "length": <int>,
                  "confidence": <float | null>
                }
              ] | null
            }
          ]
        }
      ]
    }
  ],
  "keyValuePairs": [
    {
      "key": {
        "content": "<string>",
        "boundingRegions": [ { "pageNumber": <int>, "polygon": [<float>, ...] } ] | null,
        "spans": [ { "offset": <int>, "length": <int>, "confidence": <float|null> } ] | null
      },
      "value": {
        "content": "<string>",
        "boundingRegions": [ { "pageNumber": <int>, "polygon": [<float>, ...] } ] | null,
        "spans": [ { "offset": <int>, "length": <int>, "confidence": <float|null> } ] | null
      }
    }
  ]
}

This focuses on fields most useful for:
- label/value extraction
- table traversal
- evidence mapping back to regions on the page
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _to_bbox(source: Any) -> Optional[List[float]]:
    """Return a bounding box as a list of floats, or None.

    Azure Document Intelligence typically exposes bounding boxes as a list of
    floats in reading order (x1, y1, x2, y2, ...).
    """
    if not source:
        return None

    try:
        vals = [float(v) for v in source]
    except Exception:
        return None

    return vals or None


def _normalize_spans(spans: Any) -> Optional[List[Dict[str, Any]]]:
    """Normalize spans into a simple list of dicts."""
    if not spans:
        return None

    out: List[Dict[str, Any]] = []
    for span in spans:
        # Some SDK versions expose spans as objects with .offset/.length/.confidence,
        # others as simple dicts; we handle both.
        offset = getattr(span, "offset", None)
        length = getattr(span, "length", None)
        confidence = getattr(span, "confidence", None)
        if isinstance(span, dict):
            offset = span.get("offset", offset)
            length = span.get("length", length)
            confidence = span.get("confidence", confidence)

        if offset is None or length is None:
            continue

        out.append(
            {
                "offset": int(offset),
                "length": int(length),
                "confidence": float(confidence) if confidence is not None else None,
            }
        )

    return out or None


def _normalize_bounding_regions(regions: Any) -> Optional[List[Dict[str, Any]]]:
    """Normalize bounding regions to a list of { pageNumber, polygon } dicts."""
    if not regions:
        return None

    out: List[Dict[str, Any]] = []
    for region in regions:
        if not isinstance(region, dict):
            continue
        page_number = region.get("pageNumber") or region.get("page_number")
        polygon = region.get("polygon")
        if page_number is None:
            continue
        try:
            polygon_vals = [float(v) for v in polygon] if polygon else None
        except (TypeError, ValueError):
            polygon_vals = None
        out.append(
            {
                "pageNumber": int(page_number),
                "polygon": polygon_vals,
            }
        )
    return out or None


def _normalize_key_value_element(element: Any) -> Optional[Dict[str, Any]]:
    """Normalize a key or value element (content, spans, boundingRegions)."""
    if not element or not isinstance(element, dict):
        return None
    content = element.get("content", "") or ""
    spans = _normalize_spans(element.get("spans"))
    regions = element.get("boundingRegions") or element.get("bounding_regions")
    bounding_regions = _normalize_bounding_regions(regions)
    return {
        "content": content,
        "boundingRegions": bounding_regions,
        "spans": spans,
    }


def normalize_layout_result(doc_id: str, model_id: Optional[str], result: Any) -> Dict[str, Any]:
    """Normalize a Document Intelligence layout result (dict) to the shared schema.

    Parameters
    ----------
    doc_id:
        The document identifier used throughout the pipeline.
    model_id:
        The model id used for analysis (e.g. "prebuilt-layout").
    result:
        Dict returned by DocumentIntelligenceWrapper (from result.as_dict() or
        result.to_dict()). This function is dict-first and only falls back to
        attribute access when helpful.
    """
    # Ensure we are working with a dict. If a result object was passed by mistake,
    # try as_dict() (current Document Intelligence SDK) or to_dict(), else treat as empty.
    if not isinstance(result, dict):
        if hasattr(result, "as_dict"):
            result = result.as_dict()
        elif hasattr(result, "to_dict"):
            result = result.to_dict()
        else:
            result = {}

    analyze = result.get("analyzeResult") or result

    # Pages are usually under analyzeResult["pages"]; fall back to [].
    pages_raw = analyze.get("pages") or []

    # Some shapes may keep tables only at the document level; preserve them so
    # downstream code can still consume them even if not associated with pages.
    doc_level_tables = analyze.get("tables") or []

    normalized_pages: List[Dict[str, Any]] = []

    for page in pages_raw:
        if not isinstance(page, dict):
            continue

        page_number = page.get("pageNumber")
        width = page.get("width")
        height = page.get("height")
        unit = page.get("unit")

        # Lines
        norm_lines: List[Dict[str, Any]] = []
        for line in page.get("lines") or []:
            if not isinstance(line, dict):
                continue

            content = line.get("content", "") or ""
            bbox = _to_bbox(line.get("boundingBox"))
            spans = _normalize_spans(line.get("spans"))

            norm_lines.append(
                {
                    "content": content,
                    "boundingBox": bbox,
                    "spans": spans,
                }
            )

        # Words
        norm_words: List[Dict[str, Any]] = []
        for word in page.get("words") or []:
            if not isinstance(word, dict):
                continue

            content = word.get("content", "") or ""
            bbox = _to_bbox(word.get("boundingBox"))
            confidence = word.get("confidence")

            norm_words.append(
                {
                    "content": content,
                    "boundingBox": bbox,
                    "confidence": float(confidence) if confidence is not None else None,
                }
            )

        # Tables attached to the page, if present.
        norm_tables: List[Dict[str, Any]] = []
        for table in page.get("tables") or []:
            if not isinstance(table, dict):
                continue

            row_count = table.get("rowCount")
            column_count = table.get("columnCount")
            bbox = _to_bbox(table.get("boundingBox"))
            cells = table.get("cells") or []

            norm_cells: List[Dict[str, Any]] = []
            for cell in cells:
                if not isinstance(cell, dict):
                    continue

                row_index = cell.get("rowIndex")
                column_index = cell.get("columnIndex")
                row_span = cell.get("rowSpan", 1)
                column_span = cell.get("columnSpan", 1)
                kind = cell.get("kind")
                content = cell.get("content", "") or ""
                cbbox = _to_bbox(cell.get("boundingBox"))
                spans = _normalize_spans(cell.get("spans"))

                norm_cells.append(
                    {
                        "rowIndex": int(row_index) if row_index is not None else 0,
                        "columnIndex": int(column_index) if column_index is not None else 0,
                        "rowSpan": int(row_span) if row_span is not None else 1,
                        "columnSpan": int(column_span) if column_span is not None else 1,
                        "content": content,
                        "kind": kind,
                        "boundingBox": cbbox,
                        "spans": spans,
                    }
                )

            norm_tables.append(
                {
                    "rowCount": int(row_count) if row_count is not None else 0,
                    "columnCount": int(column_count) if column_count is not None else 0,
                    "boundingBox": bbox,
                    "cells": norm_cells,
                }
            )

        normalized_pages.append(
            {
                "pageNumber": int(page_number) if page_number is not None else None,
                "width": float(width) if width is not None else None,
                "height": float(height) if height is not None else None,
                "unit": unit,
                "lines": norm_lines,
                "words": norm_words,
                "tables": norm_tables,
            }
        )

    normalized: Dict[str, Any] = {
        "docId": doc_id,
        "modelId": model_id,
        "pages": normalized_pages,
    }

    # If there are document-level tables that we could not safely associate with
    # individual pages, expose them under a separate top-level key so they are
    # still available to downstream consumers.
    if doc_level_tables:
        extra_tables: List[Dict[str, Any]] = []
        for table in doc_level_tables:
            if not isinstance(table, dict):
                continue

            row_count = table.get("rowCount")
            column_count = table.get("columnCount")
            bbox = _to_bbox(table.get("boundingBox"))
            cells = table.get("cells") or []

            norm_cells: List[Dict[str, Any]] = []
            for cell in cells:
                if not isinstance(cell, dict):
                    continue

                row_index = cell.get("rowIndex")
                column_index = cell.get("columnIndex")
                row_span = cell.get("rowSpan", 1)
                column_span = cell.get("columnSpan", 1)
                kind = cell.get("kind")
                content = cell.get("content", "") or ""
                cbbox = _to_bbox(cell.get("boundingBox"))
                spans = _normalize_spans(cell.get("spans"))

                norm_cells.append(
                    {
                        "rowIndex": int(row_index) if row_index is not None else 0,
                        "columnIndex": int(column_index) if column_index is not None else 0,
                        "rowSpan": int(row_span) if row_span is not None else 1,
                        "columnSpan": int(column_span) if column_span is not None else 1,
                        "content": content,
                        "kind": kind,
                        "boundingBox": cbbox,
                        "spans": spans,
                    }
                )

            extra_tables.append(
                {
                    "rowCount": int(row_count) if row_count is not None else 0,
                    "columnCount": int(column_count) if column_count is not None else 0,
                    "boundingBox": bbox,
                    "cells": norm_cells,
                }
            )

        normalized["documentTables"] = extra_tables

    # Key-value pairs at analyze-result level (camelCase or snake_case).
    raw_pairs = analyze.get("keyValuePairs") or analyze.get("key_value_pairs") or []
    norm_pairs: List[Dict[str, Any]] = []
    for pair in raw_pairs:
        if not isinstance(pair, dict):
            continue
        key_el = _normalize_key_value_element(pair.get("key"))
        value_el = _normalize_key_value_element(pair.get("value"))
        if key_el is not None or value_el is not None:
            norm_pairs.append(
                {
                    "key": key_el or {"content": "", "boundingRegions": None, "spans": None},
                    "value": value_el or {"content": "", "boundingRegions": None, "spans": None},
                }
            )
    normalized["keyValuePairs"] = norm_pairs

    return normalized

