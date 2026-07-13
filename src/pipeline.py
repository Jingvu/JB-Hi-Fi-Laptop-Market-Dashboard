from __future__ import annotations

import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

from .clean import clean_specs, tag_discontinued_products
from .ingest import find_latest_daily, ingest_daily
from .paths import DAILY_DIR, RESULTS_SPECS, RESULTS_SPECS_CLEANED, RESULTS_TAGGED, RESULTS_WITH_BRAND, ensure_data_dirs
from .scrape import scrape_jbhifi_laptops
from .schema import DAILY_APPEND_KEY_COLUMNS
from .specs import update_specs


MELBOURNE_TZ = ZoneInfo("Australia/Melbourne")


def scrape_today() -> None:
    ensure_data_dirs()
    today = datetime.now(MELBOURNE_TZ).date().isoformat()
    core_file = DAILY_DIR / f"{today}_results.csv"
    scrape_jbhifi_laptops(core_file)
    update_specs(core_file, RESULTS_SPECS)


def append_latest() -> None:
    ensure_data_dirs()
    daily = find_latest_daily(DAILY_DIR)
    ingest_daily(daily, RESULTS_WITH_BRAND, key_cols=DAILY_APPEND_KEY_COLUMNS)


def clean_all(keep_existing_values: bool = True) -> None:
    """Run cleaning outputs.

    By default, existing cleaned specs values are preserved. Pass
    `keep_existing_values=False` to re-apply current cleaning rules to all specs rows.
    """
    ensure_data_dirs()
    tag_discontinued_products(RESULTS_WITH_BRAND, RESULTS_TAGGED)
    clean_specs(RESULTS_SPECS, RESULTS_SPECS_CLEANED, keep_existing_values=keep_existing_values)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="JB Hi-Fi laptop market data pipeline")
    parser.add_argument(
        "step",
        choices=["scrape", "append", "clean", "all"],
        help="Pipeline step to run",
    )
    parser.add_argument(
        "--reclean-existing",
        action="store_true",
        help=(
            "Re-apply current specs cleaning rules to existing titles instead of "
            "preserving old cleaned values. Use this after approved cleaning-rule updates."
        ),
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.step in ["scrape", "all"]:
        scrape_today()
    if args.step in ["append", "all"]:
        append_latest()
    if args.step in ["clean", "all"]:
        clean_all(keep_existing_values=not args.reclean_existing)


if __name__ == "__main__":
    main()
