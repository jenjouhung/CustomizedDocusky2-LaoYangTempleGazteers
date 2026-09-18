"""Load and validate the dataset profile, then derive the runtime indexes."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "dataset" / "profile.json"
FIELD_TYPES = {"identifier", "text", "multi-text", "integer-or-text", "marked-text"}


def _unique_strings(values, label):
    if not isinstance(values, list) or not all(isinstance(value, str) and value for value in values):
        raise ValueError(f"{label} 必須是非空字串清單")
    if len(values) != len(set(values)):
        raise ValueError(f"{label} 不得包含重複欄位")
    return values


def load_profile(path=PROFILE_PATH):
    profile = json.loads(Path(path).read_text(encoding="utf-8"))
    if profile.get("schema") != 1:
        raise ValueError("dataset/profile.json schema 必須為 1")
    if not isinstance(profile.get("datasetId"), str) or not profile["datasetId"].strip():
        raise ValueError("datasetId 不得空白")
    site = profile.get("site", {})
    for key in ("title", "description", "canonicalUrl", "language", "openGraphLocale"):
        if not isinstance(site.get(key), str) or not site[key].strip():
            raise ValueError(f"site.{key} 不得空白")
    excel = profile.get("excel", {})
    if excel.get("sheet") != "first" or excel.get("headerRow") != 1 or excel.get("dataStartRow") != 2:
        raise ValueError("目前共用匯入器只支援第一個工作表、第 1 列標題及第 2 列起資料")
    for key in ("maxFileBytes", "maxExpandedBytes", "maxRecords", "maxFullTextCharacters"):
        if not isinstance(excel.get(key), int) or excel[key] < 1:
            raise ValueError(f"excel.{key} 必須是正整數")
    fields = profile.get("fields")
    if not isinstance(fields, list) or not fields:
        raise ValueError("fields 必須是非空欄位設定清單")
    names = []
    for number, field in enumerate(fields, 1):
        name, field_type = field.get("name"), field.get("type")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"fields 第 {number} 項缺少 name")
        if name.startswith(("(", "{")):
            raise ValueError(f"欄位名稱不得以 ( 或 {{ 開始：{name}")
        if field_type not in FIELD_TYPES:
            raise ValueError(f"欄位 {name} 的 type 不支援：{field_type}")
        names.append(name)
    if len(names) != len(set(names)):
        raise ValueError("fields 不得包含重複欄位名稱")
    roles = profile.get("roles", {})
    for role in ("key", "title", "fullText"):
        if roles.get(role) not in names:
            raise ValueError(f"roles.{role} 必須指向 fields 內的欄位")
    _unique_strings(roles.get("resultDisplay"), "roles.resultDisplay")
    _unique_strings(roles.get("metadataFacets"), "roles.metadataFacets")
    sort = roles.get("sort", {})
    for key in ("field", "tieBreaker"):
        if sort.get(key) not in names:
            raise ValueError(f"roles.sort.{key} 必須指向 fields 內的欄位")
    if sort.get("direction") not in ("asc", "desc"):
        raise ValueError("roles.sort.direction 只接受 asc 或 desc")
    referenced = roles["resultDisplay"] + roles["metadataFacets"]
    unknown = [name for name in referenced if name not in names]
    if unknown:
        raise ValueError("欄位角色參照未知欄位：" + "、".join(unknown))
    separator = profile.get("multiValue", {}).get("separator")
    if not isinstance(separator, str) or not separator:
        raise ValueError("multiValue.separator 不得空白")
    tags = profile.get("tagFacets", [])
    tag_names = []
    for tag in tags:
        if not isinstance(tag.get("name"), str) or not tag["name"]:
            raise ValueError("tagFacets.name 不得空白")
        if not isinstance(tag.get("label"), str) or not tag["label"]:
            raise ValueError(f"tagFacets.label 不得空白：{tag.get('name', '')}")
        tag_names.append(tag["name"])
    if len(tag_names) != len(set(tag_names)):
        raise ValueError("tagFacets.name 不得重複")
    if not isinstance(profile.get("pageSize"), int) or profile["pageSize"] < 1:
        raise ValueError("pageSize 必須是正整數")
    return profile


def derive_config(profile):
    headers = [field["name"] for field in profile["fields"]]
    positions = {name: index for index, name in enumerate(headers)}
    roles, sort = profile["roles"], profile["roles"]["sort"]
    by_type = lambda kind: [index for index, field in enumerate(profile["fields"]) if field["type"] == kind]
    return {
        "schema": 2,
        "datasetId": profile["datasetId"],
        "title": profile["site"]["title"],
        "headers": headers,
        "key": positions[roles["key"]],
        "titleField": positions[roles["title"]],
        "text": positions[roles["fullText"]],
        "sort": positions[sort["field"]],
        "sortDirection": sort["direction"],
        "tieBreak": positions[sort["tieBreaker"]],
        "display": [positions[name] for name in roles["resultDisplay"]],
        "facets": [positions[name] for name in roles["metadataFacets"]],
        "multi": by_type("multi-text"),
        "required": [index for index, field in enumerate(profile["fields"]) if field.get("required")],
        "numeric": by_type("integer-or-text"),
        "separator": profile["multiValue"]["separator"],
        "alternateSeparators": profile["multiValue"].get("alternateSeparators", []),
        "pageSize": profile["pageSize"],
        "tagFacets": profile.get("tagFacets", []),
    }


PROFILE = load_profile()
CONFIG = derive_config(PROFILE)
HEADERS = CONFIG["headers"]


if __name__ == "__main__":
    print(json.dumps({"profile": str(PROFILE_PATH), "config": CONFIG}, ensure_ascii=False, indent=2))
