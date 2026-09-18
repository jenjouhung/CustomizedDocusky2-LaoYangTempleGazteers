#!/usr/bin/env python3
"""Produce a compact, machine-readable report for a candidate dataset XLSX."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from importer import read_first_sheet

TAG_RE = re.compile(r"<([A-Za-z_][A-Za-z0-9_.-]*)\b[^<>]*>")


def inspect(path, example_limit=5):
    rows, warnings, sheet = read_first_sheet(path)
    if not rows:
        raise ValueError("第一個工作表沒有資料")
    header_values = rows[0][1]
    width = max(header_values, default=-1) + 1
    headers = [header_values.get(index) for index in range(width)]
    data_rows = [values for _, values in rows[1:] if values]
    fields = []
    tags = Counter()
    for index, name in enumerate(headers):
        values = [row.get(index) for row in data_rows]
        nonempty = [value for value in values if value is not None and str(value) != ""]
        texts = [str(value) for value in nonempty]
        distinct = {(type(value).__name__, str(value)) for value in nonempty}
        field_tags = Counter()
        examples = []
        for value in nonempty:
            text = str(value)
            observed = TAG_RE.findall(text)
            tags.update(observed)
            field_tags.update(observed)
            if len(examples) < example_limit and text not in examples:
                examples.append(text[:160])
        fields.append({
            "position": index + 1,
            "name": name,
            "nonEmpty": len(nonempty),
            "blank": len(values) - len(nonempty),
            "coverage": round(len(nonempty) / len(values), 4) if values else 0,
            "distinctNonEmpty": len(distinct),
            "allRowsNonEmptyAndUnique": bool(values) and len(nonempty) == len(values) == len(distinct),
            "numericCells": sum(isinstance(value, (int, float)) and not isinstance(value, bool) for value in nonempty),
            "averageCharacters": round(sum(map(len, texts)) / len(texts), 1) if texts else 0,
            "maxCharacters": max(map(len, texts), default=0),
            "semicolonCells": sum(";" in text for text in texts),
            "fullWidthSemicolonCells": sum("；" in text for text in texts),
            "markupCells": sum(bool(TAG_RE.search(text)) for text in texts),
            "observedTagNames": dict(field_tags),
            "examples": examples,
        })
    names = [field["name"] for field in fields]
    duplicate_names = sorted({name for name in names if names.count(name) > 1}, key=str)
    blocking = []
    if any(name is None or not isinstance(name, str) or not name.strip() for name in names):
        blocking.append("標題列包含空白或非文字欄名")
    if duplicate_names:
        blocking.append("標題列包含重複欄名：" + "、".join(map(str, duplicate_names)))
    unique_candidates = [field["name"] for field in fields if field["allRowsNonEmptyAndUnique"]]
    long_text_candidates = [
        field["name"] for field in sorted(fields, key=lambda item: (item["markupCells"], item["averageCharacters"]), reverse=True)
        if field["nonEmpty"]
    ][:5]
    facet_candidates = [
        field["name"] for field in fields
        if field["coverage"] >= 0.5
        and 1 < field["distinctNonEmpty"] <= min(200, max(2, int(len(data_rows) * 0.8)))
    ]
    multi_candidates = [
        field["name"] for field in fields
        if max(field["semicolonCells"], field["fullWidthSemicolonCells"]) >= max(2, int(field["nonEmpty"] * 0.1))
        and field["averageCharacters"] <= 120
    ]
    return {
        "file": path.name,
        "sheet": sheet,
        "rowCount": len(data_rows),
        "columnCount": width,
        "fields": fields,
        "observedTagNames": dict(tags),
        "candidates": {
            "uniqueKeys": unique_candidates,
            "longText": long_text_candidates,
            "metadataFacets": facet_candidates,
            "multiValue": multi_candidates,
        },
        "blockingIssues": blocking,
        "readerWarnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xlsx", type=Path)
    parser.add_argument("--example-limit", type=int, default=5)
    arguments = parser.parse_args()
    print(json.dumps(inspect(arguments.xlsx, arguments.example_limit), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
