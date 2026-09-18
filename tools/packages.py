"""Atomic file versions and checksum-verified backup packages."""
import datetime
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

from config import CONFIG
from importer import read_excel
from markup import PARSER_VERSION, parse_text
from site_builder import sync_index

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "workspace-data"


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    temporary.replace(path)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def manifest():
    return read(DATA / "manifest.json") if (DATA / "manifest.json").exists() else {"schema": 1, "current": None, "versions": [], "events": []}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def import_file(path):
    records, warnings, sheet = read_excel(path)
    current = manifest()
    version = "v" + str(max([int(item["id"][1:]) for item in current["versions"]] + [0]) + 1).zfill(4)
    DATA.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=DATA) as directory:
        stage, index, facets = Path(directory), {}, {}
        tag_names = {tag["name"] for tag in CONFIG["tagFacets"]}
        for number, record in enumerate(records):
            parsed = parse_text(record[CONFIG["text"]], tag_names)
            for position, character in enumerate(parsed["text"]):
                index.setdefault(character, {}).setdefault(str(number), []).append(position)
            for field in CONFIG["facets"]:
                value = record[field]
                if field in CONFIG["multi"] and value is not None:
                    values = {part.strip() for part in str(value).split(CONFIG["separator"])}
                else:
                    values = {value}
                for item in values:
                    if field in CONFIG["multi"] and item == "":
                        continue
                    facets.setdefault(str(field), {}).setdefault(json.dumps(item, ensure_ascii=False), []).append(number)
            for name, term in {(tag["name"], tag["term"]) for tag in parsed["tags"]}:
                facets.setdefault("tag:" + name, {}).setdefault(json.dumps(term, ensure_ascii=False), []).append(number)
            write(stage / "records" / f"{number}.json", record)
            write(stage / "texts" / f"{number}.json", parsed)
        write(stage / "index.json", index)
        write(stage / "facets.json", facets)
        row_fields = set(CONFIG["facets"] + [CONFIG["key"], CONFIG["sort"], CONFIG["tieBreak"]])
        write(stage / "rows.json", [{str(field): record[field] for field in row_fields} for record in records])
        metadata = {
            "id": version,
            "count": len(records),
            "created": now(),
            "source": path.name,
            "sha256": digest(path),
            "sheet": sheet,
            "headers": CONFIG["headers"],
            "warnings": warnings,
            "schema": 2,
            "parserVersion": PARSER_VERSION,
            "offsetUnit": "unicode-code-point",
            "datasetId": CONFIG["datasetId"],
        }
        write(stage / "version.json", metadata)
        write(stage / "config.json", CONFIG)
        write(stage / "checksums.json", {str(item.relative_to(stage)): digest(item) for item in stage.rglob("*") if item.is_file()})
        stage.rename(DATA / version)
    original = DATA / "originals" / f"{version}.xlsx"
    try:
        original.parent.mkdir(exist_ok=True)
        shutil.copy2(path, original)
        current["versions"].append(metadata)
        current["current"] = version
        current["events"].append({"action": "import", "version": version, "at": now()})
        write(DATA / "manifest.json", current)
    except Exception:
        shutil.rmtree(DATA / version)
        original.unlink(missing_ok=True)
        raise
    return metadata


def verify(folder):
    for version in read(folder / "manifest.json")["versions"]:
        base = folder / version["id"]
        for name, checksum in read(base / "checksums.json").items():
            path = (base / name).resolve()
            if not path.is_relative_to(base.resolve()) or digest(path) != checksum:
                raise ValueError("資料校驗失敗：" + name)


def set_current(version):
    current = manifest()
    if version not in [item["id"] for item in current["versions"]]:
        raise ValueError("未知版本")
    verify(DATA)
    current["events"].append({"action": "restore", "before": current["current"], "after": version, "at": now()})
    current["current"] = version
    write(DATA / "manifest.json", current)


def backup(automatic=False):
    verify(DATA)
    destination = ROOT / "backups"
    destination.mkdir(exist_ok=True)
    name = ("auto-" if automatic else "") + datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".zip"
    path = destination / name
    files = {str(item.relative_to(DATA)): item.read_bytes() for item in DATA.rglob("*") if item.is_file()}
    checksums = {name: hashlib.sha256(content).hexdigest() for name, content in files.items()}
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for filename, content in files.items():
            archive.writestr(filename, content)
        archive.writestr("backup-checksums.json", json.dumps(checksums))
        archive.writestr("backup-format.json", '{"schema":1,"platform":"1.0.0"}')
    if automatic:
        for old in sorted(destination.glob("auto-*.zip"), reverse=True)[5:]:
            old.unlink()
    return path


def restore(path):
    with tempfile.TemporaryDirectory(dir=ROOT) as directory, zipfile.ZipFile(path) as archive:
        base, names = Path(directory), archive.namelist()
        if len(names) != len(set(names)) or sum(item.file_size for item in archive.infolist()) > 2 * 1024**3:
            raise ValueError("無效備份")
        if json.loads(archive.read("backup-format.json")) != {"schema": 1, "platform": "1.0.0"}:
            raise ValueError("備份版本不相容")
        checksums = json.loads(archive.read("backup-checksums.json"))
        if set(names) != set(checksums) | {"backup-checksums.json", "backup-format.json"}:
            raise ValueError("備份清單不一致")
        for name, checksum in checksums.items():
            target = (base / name).resolve()
            if not target.is_relative_to(base.resolve()):
                raise ValueError("備份路徑不合法")
            content = archive.read(name)
            if hashlib.sha256(content).hexdigest() != checksum:
                raise ValueError("備份校驗失敗")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        verify(base)
        if DATA.exists():
            backup(automatic=True)
        old = ROOT / "workspace-data.previous"
        if old.exists():
            shutil.rmtree(old)
        if DATA.exists():
            DATA.rename(old)
        try:
            base.rename(DATA)
        except Exception:
            if old.exists():
                old.rename(DATA)
            raise


def public_build():
    verify(DATA)
    sync_index()
    destination = ROOT / "public-build"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(ROOT / "web", destination)
    shutil.copytree(DATA, destination / "data", ignore=shutil.ignore_patterns("originals"))
    current = manifest()
    current.pop("events", None)
    write(destination / "data" / "manifest.json", current)
    return destination
