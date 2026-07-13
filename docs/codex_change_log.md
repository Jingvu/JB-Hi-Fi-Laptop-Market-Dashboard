# Codex Change Log

## 2026-07-13 - Applied Conservative Title-Based Spec Fallbacks

Change name:
- `apply_title_based_spec_fallbacks`

Files changed:
- `src/clean.py`
- `tests/test_clean_specs.py`
- `docs/refactor_plan.md`
- `docs/codex_change_log.md`

What changed:
- Added conservative title fallback helpers for missing `Display size (inches)`, `Processor Type`, `SSD storage`, and `Total Storage`.
- Added explicit inch-marker parsing for display sizes such as `16"`, `16-inch`, and `16in`.
- Added supported processor-family parsing for Intel Core Ultra, Intel Core i, AMD Ryzen AI, and AMD Ryzen titles.
- Added storage parsing for bracketed values such as `[1TB]` and clear SSD values such as `512GB SSD`.
- Limited storage fallback to existing recognised project values: `64GB`, `128GB`, `256GB`, `512GB`, `1TB`, `2TB`, `4TB`, and `6TB`.
- Ran existing processor standardisation after fallback.
- Did not overwrite existing non-empty spec values.
- Did not change titles, deduplication keys, schemas, GPU logic, Unicode logic, notebooks, or CSV files.

Affected row counts:
- Current actual specs output shape stayed at `1640` rows and `63` columns in this workspace.
- `Display size (inches)`: `515` missing values populated.
- `Processor Type`: `20` missing values populated.
- `Processor brand`: `20` rows changed as a result of existing processor standardisation after fallback.
- `SSD storage`: `376` missing values populated.
- `Total Storage`: `385` missing values populated.
- Rows with at least one target fallback field populated: `541`.

False-positive protections:
- Does not treat `3K` as storage.
- Does not treat `120Hz` as display size or processor.
- Does not infer storage from ambiguous standalone numbers.
- Does not infer unsupported processors such as Intel Pentium Silver.
- Does not create unsupported storage categories such as `500GB`.
- Leaves titles without relevant patterns unchanged.

Validation:
- Ran focused `python -m unittest tests.test_clean_specs`; 34 tests passed.
- Ran `python -m unittest discover -s tests`; 60 tests passed.
- Ran `python -m compileall src tests`.
- Parsed working `jb_hifi.ipynb` code cells with `ast.parse`.
- Compared before/after counts for the three affected fallback areas on actual raw specs data.
- Manually reviewed representative inferred values for display size, processor, SSD storage, and total storage.
- Confirmed reference `notebooks/jb_hifi.ipynb` hash remained unchanged.

Revert plan:
- Remove title fallback constants and helpers from `src/clean.py`.
- Remove the `apply_title_spec_fallbacks(...)` call from `clean_specs_dataframe(...)`.
- Remove the focused title fallback tests.
- Remove this change-log entry and reset Group C Issue 8 in `docs/refactor_plan.md`.

## 2026-07-13 - Applied Approved High-Confidence Title-Based GPU Inference

Change name:
- `apply_high_confidence_title_gpu_inference`

Files changed:
- `src/clean.py`
- `tests/test_clean_specs.py`
- `docs/refactor_plan.md`
- `docs/codex_change_log.md`

What changed:
- Added compiled title patterns for NVIDIA RTX A-series and standard NVIDIA RTX models.
- Added `infer_gpu_from_title(...)`.
- Checked RTX A-series titles before standard RTX titles.
- Applied title inference only after existing `Graphics processor` and `Graphics card series` logic would otherwise leave the GPU as `Other`.
- Added tests for RTX with and without spaces, RTX Ti variants, explicit GeForce RTX, RTX A-series, ambiguous `arctic grey`, bare numbers, and non-overwrite behavior.
- Did not infer from `arc`, generic gaming terms, bare model numbers, lower-confidence Radeon patterns, or unsupported plain GeForce title patterns.
- Did not add a GPU-source column, change titles, change dedupe/matching keys, edit notebooks, or modify CSV files.

Affected row counts:
- Fresh-cleaned actual specs output stayed at `1638` rows and `64` columns.
- Rows moved from `GPU brand = Other` to `GPU brand = NVIDIA`: `64`.
- `Graphics processor = Other` changed from `528` to `464`.
- `GPU brand = NVIDIA` changed from `221` to `285`.
- Changed inferred values included standard RTX buckets such as `NVIDIA RTX 5070`, `NVIDIA RTX 5070 Ti`, and workstation buckets such as `NVIDIA RTX A1000`.
- Reviewed the inferred rows for false positives; none were observed in the affected set.

Validation:
- Ran focused `python -m unittest tests.test_clean_specs`; 28 tests passed.
- Ran `python -m unittest discover -s tests`; 53 tests passed.
- Ran `python -m compileall src tests`.
- Parsed working `jb_hifi.ipynb` code cells with `ast.parse`.
- Compared before/after GPU category counts on actual raw specs data.
- Confirmed rows, schema column count, and column order were unchanged.
- Confirmed reference `notebooks/jb_hifi.ipynb` hash remained unchanged.

Revert plan:
- Remove `RTX_A_TITLE_PATTERN`, `RTX_TITLE_PATTERN`, and `infer_gpu_from_title(...)`.
- Remove the title-inference call from `get_gpu_bucket(...)`.
- Remove the focused title-inference tests.
- Remove this change-log entry and reset Group C Issue 7 plus the deferred-rule status in `docs/refactor_plan.md`.

## 2026-07-13 - Applied Approved Field-Level GPU Normalization

Change name:
- `apply_field_level_gpu_normalization`

Files changed:
- `src/clean.py`
- `tests/test_clean_specs.py`
- `docs/refactor_plan.md`
- `docs/codex_change_log.md`

What changed:
- Added GPU-field text normalization before GPU bucket matching.
- Removed `®`, `™`, and literal trademark `TM` markers from `Graphics processor` text before matching.
- Added support for the identified field-level `Nvidia GeForce 4060` pattern.
- Added focused regression tests for the two identified field-level misses and existing GPU mappings.
- Did not infer GPU from `Title`.
- Did not globally normalize Unicode or mojibake.
- Did not modify titles, matching keys, CSV files, or unrelated cleaning rules.

Affected row counts:
- Fresh-cleaned actual specs output stayed at `1638` rows and `64` columns.
- `GPU brand = Other` changed from `530` to `528`.
- `GPU brand = NVIDIA` changed from `219` to `221`.
- Rows with changed `Graphics processor`: `2`.
- Rows with changed `GPU brand`: `2`.
- Changed field-level values: `NVIDIA® GeForce® RTXTM 4070 -> NVIDIA RTX 4070`; `Nvidia GeForce 4060 -> NVIDIA GeForce 4060`.

Validation:
- Ran `python -m unittest discover -s tests`; 50 tests passed.
- Ran `python -m compileall src tests`.
- Parsed working `jb_hifi.ipynb` code cells with `ast.parse`.
- Compared before/after GPU category counts on actual raw specs data.
- Confirmed rows, schema column count, and column order were unchanged.
- Confirmed reference `notebooks/jb_hifi.ipynb` hash remained unchanged.

Revert plan:
- Remove `normalize_gpu_text(...)`.
- Restore `get_gpu_bucket(...)` to matching directly against lowercased raw `Graphics processor` text.
- Remove the field-level `geforce` number match.
- Remove the focused GPU normalization tests.
- Remove this change-log entry and reset Group C Issue 6 plus the deferred-rule status in `docs/refactor_plan.md`.

## 2026-07-13 - Applied Approved Resolution Format Parsing Rules

Change name:
- `apply_resolution_format_cleaning_rules`

Files changed:
- `src/clean.py`
- `tests/test_clean_specs.py`
- `docs/refactor_plan.md`
- `docs/codex_change_log.md`

What changed:
- Added targeted `Monitor resolution` parsing for `*` separators.
- Added targeted parsing for `-by-` and `by` separators.
- Added exact space-only dimension parsing for `NNNN NNNN`.
- Preserved existing `x`, compact `2880x1800`, and multiplication-sign `×` handling.
- Added focused tests for new and existing resolution formats.
- Did not change GPU, Unicode, title, dedupe, or other cleaning rules.
- Did not modify CSV files.

Affected row counts:
- Fresh-cleaned actual specs output stayed at `1638` rows and `64` columns.
- Rows changed from `NA` to parsed `Monitor resolution`: `4`.
- Changed raw values: `2560-by-1664 -> 2560 x 1664`, `2560*1600 -> 2560 x 1600`, and two rows of `2880 1800 -> 2880 x 1800`.

Validation:
- Ran `python -m unittest discover -s tests`; 47 tests passed.
- Ran `python -m compileall src tests`.
- Parsed working `jb_hifi.ipynb` code cells with `ast.parse`.
- Confirmed rows, schema column count, and column order were unchanged on actual raw specs data.
- Confirmed exactly 4 current rows changed from `NA` to parsed resolution values.

Revert plan:
- Restore the previous `clean_resolution(...)` separator replacement and remove exact space-only parsing.
- Remove the focused tests added for the new resolution formats.
- Remove this change-log entry and reset Group C Issue 5 plus the deferred-rule status in `docs/refactor_plan.md`.

## 2026-07-12 - Applied Approved Specs Cleaning Rule Updates

Change name:
- `apply_macos_display_processor_cleaning_rules`

Files changed:
- `src/clean.py`
- `tests/test_clean_specs.py`
- `docs/refactor_plan.md`
- `docs/codex_change_log.md`

What changed:
- Mapped approved macOS values that previously fell into `Other`: generic `macOS`, Mojave, Catalina, Sierra, and Big Sur.
- Mapped approved display types that previously fell into `Other`: `Liquid Retina`, `Liquid Retina XDR`, and `WVA`.
- Cleaned real trademark symbols from processor names and preserved `Core` casing for `CoreTM`.
- Added Apple A-series processor brand handling.
- Added focused tests for the new OS, display, and processor mappings.
- Did not modify raw titles or source values.
- Did not modify `jb_hifi.ipynb` because it imports the production cleaning helpers.
- Did not modify `notebooks/jb_hifi.ipynb`.
- Did not change rows, columns, column order, deduplication, or CSV schemas.

Affected row counts:
- Fresh-cleaned actual specs output stayed at `1638` rows and `64` columns.
- `OS_family` before: `Chrome OS: 46`, `Other: 113`, `Windows: 1201`, `macOS: 278`.
- `OS_family` after: `Chrome OS: 46`, `Other: 46`, `Windows: 1201`, `macOS: 345`.
- Rows with at least one cleaned value changed: `129`.
- Changed cells by column: `Display type: 110`, `Operating system: 67`, `OS_family: 67`, `Processor brand: 8`, `Processor Type: 2`.
- `Monitor resolution` changed rows: `0`.

Validation:
- Ran `python -m unittest discover -s tests`; 45 tests passed.
- Ran `python -m compileall src tests`.
- Parsed working `jb_hifi.ipynb` code cells with `ast.parse`.
- Compared before/after counts by `OS_family` on actual raw specs data.
- Confirmed rows, columns, and column order were unchanged.

Revert plan:
- Remove the newly added macOS branches from `map_os(...)`.
- Remove the newly added `Liquid Retina`, `Liquid Retina XDR`, and `WVA` branches from `bucket_display(...)`.
- Restore processor trademark/casing cleanup and remove Apple A-series brand handling.
- Remove the focused tests added for these mappings.
- Remove this change-log entry and reset Group C Issue 4 plus the deferred-rule statuses in `docs/refactor_plan.md`.

## 2026-07-12 - Broke Specs Cleaning Into Pure Helper Steps

Change name:
- `break_specs_cleaning_into_pure_helpers`

Files changed:
- `src/clean.py`
- `tests/test_clean_specs.py`
- `docs/refactor_plan.md`
- `docs/codex_change_log.md`

What changed:
- Extracted named pure helpers from `clean_specs_dataframe(...)` for new-row marking, Copilot flags, product flags, port counts, OS fields, resolution fields, processor fields, graphics fields, and preserving existing cleaned values.
- Kept the same cleaning order and current output behavior.
- Added focused helper tests plus an end-to-end fixture that checks row count, exact column order, and representative values.
- Recorded sampled dirty-data gaps as deferred cleaning-rule changes requiring approval.
- Did not modify `jb_hifi.ipynb` because this refactor only changed imported production cleaning helpers.
- Did not modify `notebooks/jb_hifi.ipynb`.
- Did not change CSV schemas or run a live scrape.

Validation:
- Ran `python -m unittest discover -s tests`; 42 tests passed.
- Ran `python -m compileall src tests`.
- Parsed working `jb_hifi.ipynb` code cells with `ast.parse`.
- Compared the old inline specs-cleaning sequence with the new helper-composed sequence on actual raw specs data; fresh and preserve-existing modes both matched row count, columns, column order, and values.
- Confirmed reference `notebooks/jb_hifi.ipynb` hash remained unchanged.

Revert plan:
- Inline the extracted helper calls back into `clean_specs_dataframe(...)` in the same order.
- Remove the helper-specific unit tests.
- Remove the deferred cleaning-rule notes added in `docs/refactor_plan.md`.
- Remove this change-log entry and reset the Group C Issue 3 status in `docs/refactor_plan.md`.

## 2026-07-11 - Centralized Price Parsing and Specs Deduplication Policy

Change names:
- `centralize_price_parsing`
- `clarify_specs_deduplication_policy`

Files changed:
- `jb_hifi.ipynb`
- `src/clean.py`
- `tests/test_clean_specs.py`
- `docs/refactor_plan.md`
- `docs/codex_change_log.md`

What changed:
- Added `parse_price_series(...)` and reused it in discontinued-listing tagging.
- Added `dedupe_specs_by_title(...)` and reused it in specs cleaning.
- Preserved the existing price parsing behavior.
- Preserved the existing specs deduplication policy: case-insensitive title comparison, keep the last row.
- Updated the working notebook with equivalent helpers.
- Did not modify `notebooks/jb_hifi.ipynb`.
- Did not change CSV schemas.

Validation:
- Ran `python -m unittest discover -s tests`; 33 tests passed.
- Ran `python -m compileall src tests`.
- Parsed working `jb_hifi.ipynb` code cells with `ast.parse`.
- Confirmed reference `notebooks/jb_hifi.ipynb` hash remained unchanged.

Revert plan:
- Inline `parse_price_series(...)` back into `tag_discontinued_dataframe(...)`.
- Inline `dedupe_specs_by_title(...)` back into `clean_specs_dataframe(...)`.
- Revert the working notebook helper additions.
- Remove the added helper tests.
- Remove this change-log entry and reset Group C issue statuses in `docs/refactor_plan.md`.

## 2026-07-11 - Completed Initial Group B Scraping Refactors

Change names:
- `make_product_extraction_failures_observable`
- `wire_scrape_validation_into_flow`
- `split_specs_parsing_from_http_fetching`

Files changed:
- `jb_hifi.ipynb`
- `src/scrape.py`
- `src/specs.py`
- `tests/test_scrape_validation.py`
- `tests/test_specs_parser.py`
- `docs/refactor_plan.md`
- `docs/codex_change_log.md`

What changed:
- Added `extract_product_rows(...)` to return extracted rows plus skipped-card count.
- Surfaced skipped product-card extraction as a warning without changing CSV output schema.
- Added a non-live scrape-flow test proving scraped rows are validated before CSV writing.
- Extracted `parse_specs_from_html(...)` from `fetch_specs(...)`.
- Kept `fetch_specs(...)` as the HTTP wrapper and preserved its dict return shape.
- Updated the working notebook with the extraction counter and specs parser split.
- Did not modify `notebooks/jb_hifi.ipynb`.
- Did not run a live scrape or real HTTP request.

Validation:
- Ran `python -m unittest discover -s tests`; 30 tests passed.
- Ran `python -m compileall src tests`.
- Parsed working `jb_hifi.ipynb` code cells with `ast.parse`.
- Confirmed reference `notebooks/jb_hifi.ipynb` hash remained unchanged.

Revert plan:
- Inline `extract_product_rows(...)` back into the scrape list comprehension.
- Remove the skipped-card warning.
- Remove the scrape-flow validation test.
- Inline `parse_specs_from_html(...)` back into `fetch_specs(...)`.
- Revert the working notebook edits for these helpers.
- Remove `tests/test_specs_parser.py` and the added scrape tests.
- Remove this change-log entry and reset Group B issue statuses in `docs/refactor_plan.md`.

## 2026-07-11 - Separated Cleaning Transforms From File I/O

Change name:
- `separate_pure_transform_functions_from_file_io`

Files changed:
- `jb_hifi.ipynb`
- `src/clean.py`
- `tests/test_clean_specs.py`
- `docs/refactor_plan.md`
- `docs/codex_change_log.md`

What changed:
- Extracted `tag_discontinued_dataframe(...)` as a pure DataFrame transform.
- Extracted `clean_specs_dataframe(...)` as a pure DataFrame transform.
- Kept `tag_discontinued_products(...)` and `clean_specs(...)` as CSV read/write wrappers.
- Updated the working notebook with the same pure-helper separation.
- Did not modify `notebooks/jb_hifi.ipynb`.
- Did not change existing CSV schemas.

Validation:
- Ran `python -m unittest discover -s tests`; 25 tests passed.
- Ran `python -m compileall src tests`.
- Parsed working `jb_hifi.ipynb` code cells with `ast.parse`.
- Confirmed reference `notebooks/jb_hifi.ipynb` hash remained unchanged.

Revert plan:
- Inline the DataFrame transform helpers back into the CSV wrapper functions.
- Revert the working notebook helper extraction.
- Remove the new helper tests.
- Remove this change-log entry and reset the Issue 2 status in `docs/refactor_plan.md`.

## 2026-07-11 - Added Validate-Then-Write Boundary

Change name:
- `add_validate_then_write_boundary`

Files changed:
- `jb_hifi.ipynb`
- `src/scrape.py`
- `src/clean.py`
- `tests/test_scrape_validation.py`
- `tests/test_schema_validation.py`
- `docs/refactor_plan.md`
- `docs/codex_change_log.md`

What changed:
- Added pre-write validation helpers for scraped listing rows, tagged listings, and cleaned specs.
- Wired validation immediately before CSV writes in script code and the working notebook.
- Preserved current operational behavior by warning on uncertain scrape quality such as zero rows.
- Raised only for clearly unsafe-to-write structures such as missing required row fields, non-list tags, or missing required output columns.
- Did not modify `notebooks/jb_hifi.ipynb`.

Validation:
- Ran `python -m unittest discover -s tests`; 22 tests passed.
- Ran `python -m compileall src tests`.
- Parsed working `jb_hifi.ipynb` code cells with `ast.parse`.
- Confirmed reference `notebooks/jb_hifi.ipynb` hash remained unchanged.

Revert plan:
- Remove the new pre-write validation helpers and calls.
- Remove the added tests for pre-write validation.
- Revert the working notebook validation additions.
- Remove this change-log entry and reset the Issue 1 status in `docs/refactor_plan.md`.

## 2026-07-11 - Reviewed Scraping and Cleaning Refactor Candidates

Change name:
- `review_scraping_cleaning_refactor_candidates`

Files changed:
- `docs/codex_change_log.md`

What changed:
- Reviewed current scraping, product-spec extraction, cleaning, validation, error-handling, logging, constants, and side-effect boundaries.
- Identified candidate refactors for discussion only.
- Did not modify code.
- Did not modify `notebooks/jb_hifi.ipynb`.

Validation:
- Documentation-only change.

Revert plan:
- Remove this change-log entry.

## 2026-07-11 - Centralized Fragile Scraper Selectors

Change name:
- `stabilize_scraper_selectors`

Files changed:
- `jb_hifi.ipynb`
- `notebooks/jb_hifi.ipynb`
- `src/scrape.py`
- `tests/test_scrape_validation.py`
- `docs/codex_change_log.md`

What changed:
- Moved JB Hi-Fi scraper class names and CSS selectors into named constants.
- Added a short comment noting these selectors depend on storefront markup and may break after a site redesign.
- Added `validate_scraped_rows(...)`, a non-mutating helper that reports missing scraped fields, non-list tags, and unexpectedly empty scrape results.
- Mirrored the selector constants and non-mutating validation helper into both notebook copies.
- Did not add fallback selectors.
- Did not change scraping output schema.
- Did not run a live scrape.

Validation:
- Ran `python -m unittest discover -s tests`; 17 tests passed.
- Ran `python -m compileall src tests`.
- Confirmed fragile selector strings are centralized in `src/scrape.py` constants.
- Parsed all `jb_hifi.ipynb` code cells with `ast.parse`.
- Confirmed `jb_hifi.ipynb` and `notebooks/jb_hifi.ipynb` still have matching SHA-256 hashes.

Revert plan:
- Inline the selector constants back into `src/scrape.py`.
- Remove `validate_scraped_rows(...)`.
- Revert the notebook selector constants and validation helper.
- Remove `tests/test_scrape_validation.py`.
- Remove this change-log entry.

## 2026-07-11 - Updated Notebook and Tests for Targeted Safety Changes

Change names:
- `centralize_private_data_paths_scripts_only`
- `add_csv_schema_checks`
- `make_cleaned_value_preservation_explicit`

Files changed:
- `jb_hifi.ipynb`
- `notebooks/jb_hifi.ipynb`
- `src/pipeline.py`
- `tests/test_imports.py`
- `tests/test_pipeline.py`
- `tests/test_schema_validation.py`
- `docs/codex_change_log.md`

What changed:
- Updated notebook file operations to use private-data path constants instead of relative CSV paths.
- Added notebook required-column checks for listing/specs inputs.
- Added tests confirming pipeline functions use centralized private-data paths.
- Added tests confirming invalid listing/specs CSV schemas fail before output files are written.
- Made specs-cleaning preservation explicit with `KEEP_EXISTING_CLEANED_VALUES` in the notebook and `--reclean-existing` in the script CLI.

Validation:
- Ran `python -m unittest discover -s tests`; 13 tests passed.
- Ran `python -m compileall src tests`.
- Parsed all `jb_hifi.ipynb` code cells with `ast.parse`.
- Confirmed `jb_hifi.ipynb` and `notebooks/jb_hifi.ipynb` still have matching SHA-256 hashes.

Revert plan:
- Revert the notebook path/schema/preservation edits.
- Remove `tests/test_pipeline.py` and the added assertions in `tests/test_imports.py` and `tests/test_schema_validation.py`.
- Revert the `src/pipeline.py` `--reclean-existing` option.
- Remove this change-log entry.

## 2026-07-11 - Added Script Path Constants, CSV Validation, and Cleaning Policy Tests

Change names:
- `centralize_script_data_paths`
- `add_csv_schema_checks`
- `document_clean_specs_preservation_policy`

Files changed:
- `src/scrape.py`
- `src/pipeline.py`
- `src/schema.py`
- `src/ingest.py`
- `src/clean.py`
- `tests/test_schema_validation.py`
- `tests/test_clean_specs.py`
- `docs/codex_change_log.md`

What changed:
- Reused `src/schema.py` constants in scripts instead of repeating listing headers and daily append key columns.
- Added lightweight CSV schema validation helpers in `src/schema.py`.
- Added required-column checks before listing append, discontinued tagging, and specs cleaning.
- Documented `clean_specs(..., keep_existing_values=True)` as the default preservation policy.
- Added tests for schema validation and both cleaning modes: preserve existing values and re-clean all rows.

Validation:
- Ran `python -m unittest discover -s tests`.
- Ran `python -m compileall src tests`.

Revert plan:
- Revert the listed source and test files to the previous versions.
- Remove this change-log entry.

## 2026-07-11 - Added Schema Constants

Change name:
- `add_schema_constants_only`

Files changed:
- `src/schema.py`
- `tests/test_imports.py`
- `docs/codex_change_log.md`

What changed:
- Added constants for listing core columns, daily append key columns, and the specs title column.
- Did not wire these constants into pipeline logic yet, so behavior is unchanged.
- Extended smoke tests to confirm the constants are importable and contain expected values.

Validation:
- Ran `python -m unittest discover -s tests`.
- Ran `python -m compileall src tests`.

Revert plan:
- Remove `src/schema.py`.
- Remove the schema assertions from `tests/test_imports.py`.
- Remove this change-log entry.

## 2026-07-11 - Added Import Smoke Tests

Change name:
- `add_import_smoke_tests`

Files changed:
- `tests/test_imports.py`
- `docs/codex_change_log.md`

What changed:
- Added a small `unittest` smoke test that imports the public pipeline modules.
- Added path sanity checks for the repo root and private data directory constants.

Validation:
- Ran `python -m unittest discover -s tests`.
- Ran `python -m compileall src tests`.

Revert plan:
- Remove `tests/test_imports.py`.
- Remove this change-log entry.

## 2026-07-11 - Cleared Notebook Outputs

Change name:
- `clear_public_notebook_outputs`

Files changed:
- `jb_hifi.ipynb`
- `notebooks/jb_hifi.ipynb`
- `docs/codex_change_log.md`

What changed:
- Cleared saved code-cell outputs and execution counts from both notebook copies.
- Kept notebook source cells unchanged.

Validation:
- Compared notebook source hash before and after clearing outputs.
- Confirmed both notebooks have zero saved outputs and zero execution counts.

Revert plan:
- Restore notebook files from Git or a local backup if saved outputs are needed.
- Remove this change-log entry.

## 2026-07-11 - Protected Private Data Outputs

Change name:
- `protect_private_data_outputs`

Files changed:
- `.gitignore`
- `docs/codex_change_log.md`

What changed:
- Added explicit ignore rules for local private-data folders: `private_data/`, `jb_hifi_private_data/`, `jb_daily_data/`, and `jb_backup_data/`.
- Added `*.xls` alongside existing spreadsheet/data-output ignore rules.

Validation:
- Ran `git status --short`; no CSV data files appeared.
- Ran `git check-ignore -v` for representative private data paths and confirmed they match `.gitignore`.

Revert plan:
- Remove the added `.gitignore` lines.
- Remove this change-log entry.

## 2026-07-11 - Confirmed NumPy Dependency

Change name:
- `add_numpy_dependency`

Files changed:
- `docs/codex_change_log.md`

What changed:
- Confirmed the active notebook import cell already contains `import numpy as np`.
- No notebook edit was required.

Validation:
- Parsed `jb_hifi.ipynb` and asserted the import exists.
- Imported NumPy successfully in the project virtual environment.
- Confirmed notebook hash remained unchanged.

Revert plan:
- Remove this change-log entry.

## 2026-07-11 - Created Low-Risk Refactor Implementation Plan

Change name:
- `create_low_risk_refactor_plan`

Files changed:
- `docs/refactor_plan.md`
- `docs/codex_change_log.md`

What changed:
- Created a low-risk implementation plan for issues unlikely to change project behavior.
- Split the work into small, isolated, reviewable, and revertible changes.
- Added validation and revert instructions for each planned change.

Validation:
- Documentation-only change.
- No notebook or pipeline code was edited.

Revert plan:
- Remove `docs/refactor_plan.md`.
- Remove this change-log entry.

## 2026-07-11 - Notebook Refactor Audit

Scope:
- Reviewed `jb_hifi.ipynb` without editing the notebook.
- Confirmed `jb_hifi.ipynb` and `notebooks/jb_hifi.ipynb` are identical copies by SHA-256 hash at audit time.
- Created this change log as the first documented audit entry.

Prioritized issues:

1. Side-effect cells are mixed with analysis cells
   - Why it matters: running the notebook can scrape live data, append to the master CSV, create backups, and rewrite cleaned outputs.
   - Risk if not fixed: accidental "Run All" can duplicate or mutate production data.
   - Proposed refactor: move side-effect operations behind explicit pipeline commands and leave the notebook for exploration.
   - Test/validation method: run command help and dry-run style checks before executing mutating commands.
   - Revert plan: restore the notebook-only workflow and remove the command wrappers.
   - Suggested change name: isolate_notebook_side_effects

2. Hard-coded relative data paths
   - Why it matters: the notebook assumes CSVs are in the current working directory.
   - Risk if not fixed: code fails or writes files into the wrong folder after separating public code from private data.
   - Proposed refactor: centralize paths in a small path helper that points to the private data directory.
   - Test/validation method: verify resolved paths and confirm raw/processed/backups are read from the private folder.
   - Revert plan: restore direct relative string paths in notebook cells.
   - Suggested change name: centralize_private_data_paths

3. Missing explicit NumPy import
   - Why it matters: the cleaning cell uses `np.where` and `np.nan`.
   - Risk if not fixed: a fresh kernel can fail during specs cleaning.
   - Proposed refactor: add `import numpy as np` in the cleaning module or imports cell.
   - Test/validation method: restart kernel or run module imports from a clean process.
   - Revert plan: remove the NumPy import if the logic is rewritten to avoid NumPy.
   - Suggested change name: add_numpy_dependency

4. Scraper depends on fragile website selectors
   - Why it matters: JB Hi-Fi class names and test IDs can change without warning.
   - Risk if not fixed: scraper may return partial data or empty files.
   - Proposed refactor: isolate selectors as constants and add row-count/schema validation after scraping.
   - Test/validation method: run a limited scrape and assert required columns and minimum product count.
   - Revert plan: restore selectors inline in extraction functions.
   - Suggested change name: stabilize_scraper_selectors

5. Specs extraction uses regex against embedded JavaScript
   - Why it matters: regex parsing can fail if the site changes JSON formatting or nesting.
   - Risk if not fixed: specs file may silently miss product details.
   - Proposed refactor: isolate parser logic and add validation for expected JSON keys.
   - Test/validation method: test parser against saved product-page HTML samples.
   - Revert plan: restore current `fetch_specs` implementation.
   - Suggested change name: harden_specs_parser

6. Cleaning logic preserves old cleaned values for existing rows
   - Why it matters: updated cleaning rules do not automatically apply to existing products.
   - Risk if not fixed: cleaned output may mix old and new transformation logic.
   - Proposed refactor: separate automated cleaning from manual override preservation.
   - Test/validation method: compare full re-clean output against override-preserved output.
   - Revert plan: keep the current old-value restoration step.
   - Suggested change name: separate_cleaning_from_overrides

7. Duplicate notebook copies exist
   - Why it matters: edits may be made to one copy while the other becomes stale.
   - Risk if not fixed: confusion about which notebook is canonical.
   - Proposed refactor: keep one canonical notebook location and remove or ignore the duplicate.
   - Test/validation method: compare hashes before removing the duplicate.
   - Revert plan: restore the duplicate notebook from Git or local copy.
   - Suggested change name: choose_canonical_notebook

8. Large CSV outputs are easy to commit accidentally
   - Why it matters: full scraped data should remain private and may make the repo heavy.
   - Risk if not fixed: private data leaks into the public repository.
   - Proposed refactor: keep `.gitignore` rules for CSV/data outputs and store real data outside the repo.
   - Test/validation method: run `git status --short` and confirm no CSVs are staged or untracked.
   - Revert plan: remove ignore rules if intentionally publishing a small sample dataset.
   - Suggested change name: protect_private_data_outputs

9. Notebook contains saved outputs from previous runs
   - Why it matters: saved outputs can make diffs noisy and may expose local file names or scrape results.
   - Risk if not fixed: public commits become harder to review and may reveal private operational details.
   - Proposed refactor: clear notebook outputs before publishing or keep an output-free public notebook.
   - Test/validation method: inspect notebook metadata/output counts before commit.
   - Revert plan: restore output cells from local backup if needed for presentation.
   - Suggested change name: clear_public_notebook_outputs

10. No automated validation around CSV schemas
    - Why it matters: append and clean steps assume matching columns and expected fields.
    - Risk if not fixed: schema drift can break the pipeline or corrupt outputs.
    - Proposed refactor: add lightweight schema checks before append and after cleaning.
    - Test/validation method: run validation against current raw, processed, and cleaned CSVs.
    - Revert plan: remove schema assertions and rely on manual inspection.
    - Suggested change name: add_csv_schema_checks
