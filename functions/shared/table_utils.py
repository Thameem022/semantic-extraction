"""Utilities to serialize Azure Document Intelligence tables as Markdown for LLM context."""

from __future__ import annotations

import re
from typing import Any


def cell_page_number(cell: dict[str, Any]) -> int:
    """Resolve page number from a table cell (boundingRegions, then pageNumber, else 1)."""
    regions = cell.get("boundingRegions") or cell.get("bounding_regions")
    if isinstance(regions, list) and regions:
        first = regions[0]
        if isinstance(first, dict):
            pn = first.get("pageNumber")
            if pn is not None:
                return int(pn)

    pn = cell.get("pageNumber")
    if pn is not None:
        return int(pn)
    return 1


def _sanitize_cell_content(content: Any) -> str:
    """Replace internal newlines/carriage returns with a space; strip ends."""
    text = str(content or "")
    text = re.sub(r"[\n\r]+", " ", text)
    return text.strip()


def _coerce_polygon(raw_polygon: Any) -> list[float]:
    if not isinstance(raw_polygon, list):
        return [0.0] * 8
    values: list[float] = []
    for item in raw_polygon[:8]:
        try:
            values.append(float(item))
        except (TypeError, ValueError):
            values.append(0.0)
    if len(values) < 8:
        values.extend([0.0] * (8 - len(values)))
    return values


def _table_anchor(table: dict[str, Any], cells: list[dict[str, Any]]) -> tuple[int, list[float]]:
    """Resolve a table-level anchor bbox, falling back to first cell geometry."""
    regions = table.get("boundingRegions") or table.get("bounding_regions")
    if isinstance(regions, list) and regions:
        first = regions[0]
        if isinstance(first, dict):
            page_number = int(first.get("pageNumber", 1) or 1)
            polygon = _coerce_polygon(first.get("polygon"))
            if any(v != 0.0 for v in polygon):
                return page_number, polygon

    first_cell = cells[0] if cells and isinstance(cells[0], dict) else {}
    page_number = cell_page_number(first_cell) if first_cell else 1
    cell_regions = first_cell.get("boundingRegions") or first_cell.get("bounding_regions")
    if isinstance(cell_regions, list) and cell_regions:
        region = cell_regions[0]
        if isinstance(region, dict):
            polygon = _coerce_polygon(region.get("polygon"))
            if any(v != 0.0 for v in polygon):
                return page_number, polygon

    return page_number, _coerce_polygon(first_cell.get("boundingBox")) if first_cell else [0.0] * 8


def serialize_tables_for_llm(layout_json: dict, max_pages: int = 5) -> list[dict[str, Any]]:
    """Return per-table markdown with page/bbox metadata for LLM candidate anchoring."""
    raw = layout_json.get("documentTables")
    if not isinstance(raw, list) or not raw:
        return []

    blocks: list[dict[str, Any]] = []
    table_index = 0

    for table in raw:
        if not isinstance(table, dict):
            continue

        row_count = int(table.get("rowCount") or 0)
        col_count = int(table.get("columnCount") or 0)
        if row_count < 2 or col_count < 1:
            continue

        cells = table.get("cells") or []
        if not cells or not isinstance(cells[0], dict):
            continue

        page_number = cell_page_number(cells[0])
        if page_number > max_pages:
            continue

        table_index += 1
        grid: list[list[str]] = [[""] * col_count for _ in range(row_count)]

        for cell in cells:
            if not isinstance(cell, dict):
                continue
            r = int(cell.get("rowIndex", 0) or 0)
            c = int(cell.get("columnIndex", 0) or 0)
            if r < 0 or r >= row_count or c < 0 or c >= col_count:
                continue
            grid[r][c] = _sanitize_cell_content(cell.get("content", ""))

        title = f"## Table {table_index} (Page {page_number})"
        lines: list[str] = [title]
        for ri, row in enumerate(grid):
            lines.append("| " + " | ".join(row) + " |")
            if ri == 0:
                lines.append("| " + " | ".join(["---"] * col_count) + " |")

        anchor_page, anchor_bbox = _table_anchor(table, cells)
        blocks.append(
            {
                "title": title,
                "markdown": "\n".join(lines),
                "pageNumber": anchor_page,
                "boundingBox": anchor_bbox,
            }
        )

    return blocks


def flatten_tables_to_markdown(layout_json: dict, max_pages: int = 5) -> str:
    """Serialize ``documentTables`` from layout JSON into pipe-style Markdown tables.

    Output is suitable for inclusion in LLM prompts: section headers per table,
    GitHub-flavored table rows, and a separator after the header row.
    """
    blocks = serialize_tables_for_llm(layout_json, max_pages=max_pages)
    if not blocks:
        return ""
    return "\n\n".join(str(block.get("markdown") or "") for block in blocks)


def serialize_kv_pairs_for_llm(layout_json: dict) -> str:
    """Render ``keyValuePairs`` as ``Key: Value (Page N)`` lines for LLM context."""
    pairs = layout_json.get("keyValuePairs")
    if not isinstance(pairs, list) or not pairs:
        return ""

    lines: list[str] = []
    for pair in pairs:
        if not isinstance(pair, dict):
            continue
        key_obj = pair.get("key") or {}
        value_obj = pair.get("value") or {}
        key_text = str(key_obj.get("content") or "").strip()
        raw_value = str(value_obj.get("content") or "").strip()
        if not key_text:
            continue

        page_number = 1
        regions = key_obj.get("boundingRegions")
        if isinstance(regions, list) and regions:
            first = regions[0]
            if isinstance(first, dict):
                page_number = int(first.get("pageNumber", 1) or 1)

        display_value = raw_value if raw_value else "(empty)"
        sanitized_value = re.sub(r"[\n\r]+", " ", display_value).strip()
        lines.append(f"{key_text} {sanitized_value} (Page {page_number})")

    return "\n".join(lines)


def serialize_pages_for_llm(layout_json: dict, max_pages: int = 30) -> str:
    """Render ``pages[].lines`` as plain text blocks per page for LLM context."""
    pages = layout_json.get("pages")
    if not isinstance(pages, list) or not pages:
        return ""

    sections: list[str] = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        page_number = int(page.get("pageNumber", 1) or 1)
        if page_number > max_pages:
            continue

        page_lines: list[str] = []
        for line in page.get("lines") or []:
            if not isinstance(line, dict):
                continue
            content = str(line.get("content") or "").strip()
            if content:
                page_lines.append(content)

        if page_lines:
            sections.append(f"--- Page {page_number} ---\n" + "\n".join(page_lines))

    return "\n\n".join(sections)
