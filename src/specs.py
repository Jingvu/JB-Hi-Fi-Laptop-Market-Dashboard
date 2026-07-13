from __future__ import annotations

import csv
import json
import os
import random
import re
import time
import unicodedata
from html import unescape
from pathlib import Path

import requests


def parse_specs_from_html(html: str) -> dict[str, str]:
    pattern = r"window\.themeConfig\(\s*['\"]([^'\"]+)['\"]\s*,\s*(\{.*?\})\s*\)\s*;"
    matches = re.findall(pattern, html, re.DOTALL)

    block = None
    for key, js in matches:
        if key.strip() == "product.metafields":
            block = js
            break
    if not block:
        return {}

    try:
        data = json.loads(unescape(block))
        specs_list = data["online_product"]["value"]["Display"]["SpecificationDetails"]
    except Exception:
        return {}

    return {
        spec["Name"]: ", ".join(map(str, spec.get("Values", [])))
        for spec in specs_list
        if spec.get("Name") and spec.get("Values")
    }


def fetch_specs(product_url: str) -> dict[str, str]:
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(product_url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception:
        return {}

    return parse_specs_from_html(response.text)


def normalize_title(title: str) -> str:
    return unicodedata.normalize("NFKC", unescape(title.strip().lower()))


def update_specs(core_file: str | Path, specs_file: str | Path, limit: int | None = None, delay: float = 1, jitter: float = 0.5) -> Path:
    core_path = Path(core_file)
    specs_path = Path(specs_file)

    with core_path.open(newline="", encoding="utf-8-sig") as file:
        core_rows = list(csv.DictReader(file))

    title_to_link = {normalize_title(row["Title"]): row["Link"] for row in core_rows}

    existing: dict[str, dict[str, str]] = {}
    if specs_path.exists():
        with specs_path.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames:
                reader.fieldnames = [name.lstrip("\ufeff") for name in reader.fieldnames]
            for row in reader:
                existing[normalize_title(row["Title"])] = {
                    key: value for key, value in row.items() if key != "Title"
                }

    new_titles = [title for title in title_to_link if title not in existing]
    if limit:
        new_titles = new_titles[:limit]
    print(f"Found {len(new_titles)} new laptops to fetch specs for.")

    for title in new_titles:
        existing[title] = fetch_specs(title_to_link[title])
        time.sleep(delay + random.random() * jitter)

    all_keys = sorted({key for specs in existing.values() for key in specs})
    specs_path.parent.mkdir(parents=True, exist_ok=True)
    with specs_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["Title"] + all_keys)
        for title, specs in existing.items():
            row_vals = []
            for key in all_keys:
                raw = specs.get(key, "")
                text = ", ".join(map(str, raw)) if isinstance(raw, (list, tuple)) else str(raw)
                row_vals.append(unicodedata.normalize("NFKC", unescape(text)))
            writer.writerow([unicodedata.normalize("NFKC", unescape(title))] + row_vals)

    print(f"Specs data saved to {specs_path}")
    return specs_path
