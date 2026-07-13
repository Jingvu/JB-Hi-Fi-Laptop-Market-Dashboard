from __future__ import annotations

import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = REPO_ROOT.parent / "jb_hifi_private_data"
DATA_DIR = Path(os.environ.get("JB_HIFI_DATA_DIR", DEFAULT_DATA_DIR)).resolve()

RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
BACKUP_DIR = DATA_DIR / "backups"

DAILY_DIR = RAW_DIR / "jb_daily_data"
DAILY_RESULTS_PATTERN = "*_results.csv"

RAW_RESULTS = RAW_DIR / "results.csv"
RESULTS_SPECS = RAW_DIR / "results_specs.csv"

RESULTS_WITH_BRAND = PROCESSED_DIR / "results_with_brand.csv"
RESULTS_TAGGED = PROCESSED_DIR / "results_tagged.csv"
RESULTS_SPECS_CLEANED = PROCESSED_DIR / "results_specs_cleaned_all.csv"

MASTER_BACKUP_DIR = BACKUP_DIR / "jb_backup_data"


def ensure_data_dirs() -> None:
    for path in [RAW_DIR, PROCESSED_DIR, DAILY_DIR, BACKUP_DIR, MASTER_BACKUP_DIR]:
        path.mkdir(parents=True, exist_ok=True)
