"""Synchronize static site metadata from dataset/profile.json."""
from __future__ import annotations

import html
import re
from pathlib import Path

from config import PROFILE, ROOT


def _replace_once(source, pattern, replacement, label):
    updated, count = re.subn(pattern, lambda _match: replacement, source, count=1, flags=re.DOTALL)
    if count != 1:
        raise ValueError(f"無法更新網站欄位：{label}")
    return updated


def render_index(source):
    site = PROFILE["site"]
    title = html.escape(site["title"], quote=True)
    description = html.escape(site["description"], quote=True)
    canonical_url = html.escape(site["canonicalUrl"], quote=True)
    language = html.escape(site["language"], quote=True)
    locale = html.escape(site["openGraphLocale"], quote=True)
    source = _replace_once(source, r'<html lang="[^"]*">', f'<html lang="{language}">', "language")
    source = _replace_once(source, r"<title>.*?</title>", f"<title>{title}</title>", "title")
    replacements = {
        '<meta name="description"': description,
        '<meta property="og:locale"': locale,
        '<meta property="og:site_name"': title,
        '<meta property="og:title"': title,
        '<meta property="og:description"': description,
        '<meta property="og:url"': canonical_url,
        '<meta name="twitter:title"': title,
        '<meta name="twitter:description"': description,
    }
    for prefix, value in replacements.items():
        pattern = re.escape(prefix) + r' content="[^"]*">'
        source = _replace_once(source, pattern, f'{prefix} content="{value}">', prefix)
    source = _replace_once(source, r'<h1 id="title">.*?</h1>', f'<h1 id="title">{title}</h1>', "heading")
    return source


def sync_index(path=None):
    path = Path(path or ROOT / "web" / "index.html")
    original = path.read_text(encoding="utf-8")
    updated = render_index(original)
    if updated != original:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(updated, encoding="utf-8")
        temporary.replace(path)
    return path


if __name__ == "__main__":
    print(sync_index())
