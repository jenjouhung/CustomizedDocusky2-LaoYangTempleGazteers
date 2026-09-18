#!/usr/bin/env python3
"""Create a fresh platform dataset from the configured profile and one XLSX file."""
from __future__ import annotations

import argparse
import datetime
import json
import shutil
import tempfile
from pathlib import Path

import packages
from config import CONFIG


def create(source, replace=False, build=True):
    source = source.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"找不到 Excel：{source}")
    # Validate before changing the existing dataset.
    packages.read_excel(source)
    original_data = packages.DATA
    if original_data.exists() and not replace:
        raise ValueError("workspace-data 已存在；在新的專案副本中確認要取代後，請加上 --replace")
    staging_parent = Path(tempfile.mkdtemp(prefix="dataset-build-", dir=packages.ROOT))
    staging_data = staging_parent / "workspace-data"
    previous = None
    try:
        packages.DATA = staging_data
        metadata = packages.import_file(source)
        packages.verify(staging_data)
        packages.DATA = original_data
        if original_data.exists():
            packages.backup()
            stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            previous = packages.ROOT / "backups" / f"previous-dataset-{stamp}"
            original_data.rename(previous)
        staging_data.rename(original_data)
        packages.DATA = original_data
        if build:
            packages.public_build()
        return {"datasetId": CONFIG["datasetId"], "version": metadata["id"], "count": metadata["count"], "previous": str(previous) if previous else None}
    except Exception:
        packages.DATA = original_data
        if previous is not None and previous.exists() and not original_data.exists():
            previous.rename(original_data)
        raise
    finally:
        packages.DATA = original_data
        if staging_parent.exists():
            shutil.rmtree(staging_parent)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xlsx", type=Path)
    parser.add_argument("--replace", action="store_true", help="備份並取代既有 workspace-data")
    parser.add_argument("--no-build", action="store_true", help="不建立 public-build")
    arguments = parser.parse_args()
    print(json.dumps(create(arguments.xlsx, arguments.replace, not arguments.no_build), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
