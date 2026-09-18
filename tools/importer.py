"""Read the first XLSX sheet and validate it against the dataset profile."""
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile

from config import CONFIG, PROFILE
from markup import parse_text

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def read_first_sheet(path):
    limits = PROFILE["excel"]
    if path.stat().st_size > limits["maxFileBytes"]:
        raise ValueError(f"Excel 超過 {limits['maxFileBytes']} bytes")
    warnings = []
    with zipfile.ZipFile(path) as archive:
        if sum(item.file_size for item in archive.infolist()) > limits["maxExpandedBytes"]:
            raise ValueError(f"Excel 解壓大小超過安全上限 {limits['maxExpandedBytes']} bytes")
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(text.text or "" for text in item.findall(".//m:t", NS)) for item in root]
        sheets = ET.fromstring(archive.read("xl/workbook.xml")).find("m:sheets", NS)
        if sheets is None or not len(sheets):
            raise ValueError("Excel 沒有工作表")
        first = sheets[0]
        relation_id = first.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        relations = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        target = next(relation.get("Target") for relation in relations if relation.get("Id") == relation_id)
        target = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
        rows = []
        xml = ET.fromstring(archive.read(target))
        for row in xml.findall(".//m:sheetData/m:row", NS):
            values = {}
            for cell in row:
                reference, column = cell.get("r", ""), 0
                for character in re.sub("[0-9]", "", reference):
                    column = column * 26 + ord(character) - 64
                if cell.find("m:f", NS) is not None:
                    raise ValueError(f"{first.get('name')} 第{row.get('r')}列 {reference}：不支援公式，請提供確定值")
                value_node, cell_type = cell.find("m:v", NS), cell.get("t")
                value = value_node.text if value_node is not None else None
                if cell_type == "s":
                    value = shared[int(value)]
                elif cell_type == "inlineStr":
                    value = "".join(text.text or "" for text in cell.findall(".//m:t", NS))
                elif value is not None and cell_type not in ("str", "e"):
                    value = float(value)
                    value = int(value) if value.is_integer() else value
                if value is not None:
                    values[column - 1] = value
            rows.append((int(row.get("r")), values))
    return rows, warnings, first.get("name")


def read_excel(path):
    rows, warnings, sheet_name = read_first_sheet(path)
    if not rows or rows[0][0] != PROFILE["excel"]["headerRow"]:
        raise ValueError("第1列必須是標題列")
    expected, header = CONFIG["headers"], rows[0][1]
    actual = [header.get(index) for index in range(max(header, default=-1) + 1)]
    if actual != expected:
        raise ValueError("欄位數、名稱或順序與 dataset/profile.json 不符；請回到資料規格修訂流程")
    records, seen = [], set()
    last = max((number for number, values in rows[1:] if values), default=1)
    for number, values in rows[1:]:
        if not values:
            if number < last:
                warnings.append(f"第{number}列：空白列，不形成紀錄")
            continue
        if max(values) >= len(expected):
            raise ValueError(f"第{number}列有額外欄位")
        record = [values.get(index) for index in range(len(expected))]
        for index in CONFIG["required"]:
            if record[index] is None or not str(record[index]).strip():
                raise ValueError(f"第{number}列 {expected[index]} 不得空白")
        key = str(record[CONFIG["key"]])
        if key in seen:
            raise ValueError(f"第{number}列 唯一鍵重複：{key}")
        seen.add(key)
        if len(str(record[CONFIG["text"]])) > PROFILE["excel"]["maxFullTextCharacters"]:
            raise ValueError(f"第{number}列 全文超過{PROFILE['excel']['maxFullTextCharacters']}字元")
        try:
            parse_text(record[CONFIG["text"]], {tag["name"] for tag in CONFIG["tagFacets"]})
        except ValueError as error:
            raise ValueError(f"{sheet_name} 第{number}列 {expected[CONFIG['text']]}：{error}") from error
        for index, value in enumerate(record):
            if value is None:
                warnings.append(f"第{number}列 {expected[index]}：空白值")
            if index in CONFIG["multi"] and value is not None:
                raw = str(value)
                parts = [part.strip() for part in raw.split(CONFIG["separator"])]
                has_alternate = any(separator in raw for separator in CONFIG["alternateSeparators"])
                if "" in parts or len(parts) != len(set(parts)) or has_alternate:
                    warnings.append(f"第{number}列 {expected[index]}：空項、重複項或疑似分隔符號")
        records.append(record)
    if len(records) > PROFILE["excel"]["maxRecords"]:
        raise ValueError(f"紀錄超過{PROFILE['excel']['maxRecords']}筆")
    return records, warnings, sheet_name
