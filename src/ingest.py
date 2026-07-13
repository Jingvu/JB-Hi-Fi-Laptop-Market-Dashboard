from __future__ import annotations

import glob
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from .paths import DAILY_RESULTS_PATTERN, MASTER_BACKUP_DIR
from .schema import DAILY_APPEND_KEY_COLUMNS, LISTING_CORE_COLUMNS, require_columns


MELBOURNE_TZ = ZoneInfo("Australia/Melbourne")


def find_latest_daily(dir_path: str | Path, pattern: str = DAILY_RESULTS_PATTERN) -> Path:
    paths = glob.glob(str(Path(dir_path) / pattern))
    if not paths:
        raise FileNotFoundError(f"No files found in {dir_path}/{pattern}")
    return Path(max(paths, key=lambda path: Path(path).stat().st_mtime))


def ingest_daily(daily_file: str | Path, master_file: str | Path, key_cols: list[str] | None = None, backup_dir: str | Path = MASTER_BACKUP_DIR) -> Path | None:
    daily_path = Path(daily_file)
    master_path = Path(master_file)
    backup_path = Path(backup_dir)
    key_cols = key_cols or DAILY_APPEND_KEY_COLUMNS

    df_daily = pd.read_csv(daily_path, encoding="utf-8-sig")
    if len(df_daily) == 0:
        raise ValueError(f"{daily_path} is empty")
    require_columns(list(df_daily.columns), LISTING_CORE_COLUMNS, "daily listings")
    require_columns(list(df_daily.columns), key_cols, "daily listings")

    df_master = pd.read_csv(master_path, encoding="utf-8-sig")
    require_columns(list(df_master.columns), LISTING_CORE_COLUMNS, "master listings")
    require_columns(list(df_master.columns), key_cols, "master listings")
    if list(df_daily.columns) != list(df_master.columns):
        raise ValueError("Daily and master columns do not match")

    dupes = pd.merge(
        df_daily[key_cols].drop_duplicates(),
        df_master[key_cols].drop_duplicates(),
        on=key_cols,
        how="inner",
    )
    if not dupes.empty:
        print(f"Found {len(dupes)} duplicate rows. Aborting.")
        return None

    today = datetime.now(MELBOURNE_TZ).date().isoformat()
    backup_path.mkdir(parents=True, exist_ok=True)
    backup_file = backup_path / f"jb_bak_{today}.csv"
    shutil.copy(master_path, backup_file)
    print(f"Backup saved to {backup_file}")

    old_master_rows = len(df_master)
    df_new_master = pd.concat([df_master, df_daily], ignore_index=True)
    df_new_master.to_csv(master_path, index=False, encoding="utf-8-sig")

    expected = len(df_daily) + old_master_rows
    if len(df_new_master) != expected:
        raise RuntimeError("Number of rows does not match after append")

    print(f"Appended {len(df_daily)} rows. New master row-count: {len(df_new_master)}")
    return master_path
