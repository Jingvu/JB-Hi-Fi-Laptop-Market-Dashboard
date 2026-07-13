from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from .schema import LISTING_CORE_COLUMNS, SPECS_TITLE_COLUMN, require_columns


DROP_SPEC_COLUMNS = [
    "Backlit keyboard", "Contains button battery", "PC Gaming Device", "Microsoft Surface type",
    "Tablet Type", "Network compatibility", "Wi-Fi", "Charge port", "RAM module configuration",
    "Expandable memory slot(s)", "Expandable storage type", "Battery WHr", "Battery capacity (mAh)", "Battery life",
    "TOPS (AI metric)", "Processor Memory Cache", "Device screen size (inches)", "Response Time (ms)",
    "Aspect ratio", "Graphics memory", "Flash storage", "Ethernet / LAN ports", "Intel Evo device",
    "Internal memory", "Manufacturer's Warranty", "Memory type", "Mini HDMI ports",
    "Mouse and keyboard", "Power supply type", "Processor Clock Speed (GHz)",
    "Processor Max. Clock Speed (GHz)", "RAM speeds", "RAM type", "Refresh Rate (Hz)",
    "SSD form factor", "Surface Connect ports", "eMMC storage", "Processor Model Number",
]

RTX_A_TITLE_PATTERN = re.compile(r"\brtx\s+a\s*(\d{3,4})\b", re.IGNORECASE)
RTX_TITLE_PATTERN = re.compile(r"\brtx\s*-?\s*(\d{3,4})\s*(ti)?\b", re.IGNORECASE)
TITLE_DISPLAY_SIZE_PATTERN = re.compile(r'(?<![\d.])(1[0-9](?:\.\d)?|2[0-4](?:\.\d)?)\s*(?:"|inch\b|in\b)', re.IGNORECASE)
TITLE_STORAGE_BRACKET_PATTERN = re.compile(r"\[(\d+(?:\.\d+)?)\s*(tb|gb)\]", re.IGNORECASE)
TITLE_STORAGE_SSD_PATTERN = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*(tb|gb)\s+ssd\b|\bssd\s*(\d+(?:\.\d+)?)\s*(tb|gb)\b",
    re.IGNORECASE,
)
TITLE_STORAGE_ALLOWED_VALUES = {"64GB", "128GB", "256GB", "512GB", "1TB", "2TB", "4TB", "6TB"}
TITLE_PROCESSOR_PATTERNS = [
    (re.compile(r"\bintel\s+core\s+ultra\s+([579])\b", re.IGNORECASE), "Intel Core Ultra {group1}"),
    (re.compile(r"\bintel\s+core\s+i([3579])\b", re.IGNORECASE), "Intel Core i{group1}"),
    (re.compile(r"\bamd\s+ryzen\s+ai\s+([579])\b", re.IGNORECASE), "AMD Ryzen AI {group1}"),
    (re.compile(r"\bamd\s+ryzen\s+([3579])\b", re.IGNORECASE), "AMD Ryzen {group1}"),
]


def validate_tagged_listings_before_write(df: pd.DataFrame) -> None:
    require_columns(
        list(df.columns),
        LISTING_CORE_COLUMNS + ["Final appear day", "Discontinued"],
        "tagged listings",
    )


def validate_clean_specs_before_write(df: pd.DataFrame) -> None:
    require_columns(list(df.columns), [SPECS_TITLE_COLUMN], "cleaned specs")


def parse_price_series(series: pd.Series) -> pd.Series:
    return series.str.replace(r"[\$,]", "", regex=True).astype("float64")


def dedupe_specs_by_title(df: pd.DataFrame, keep: str = "last") -> pd.DataFrame:
    df = df.copy()
    df["Title_lower"] = df[SPECS_TITLE_COLUMN].str.lower()
    dup_count = df.duplicated(subset=["Title_lower"],keep=keep).sum()
    print(f"Found {dup_count} duplicate rows")
    df = df.drop_duplicates(subset=["Title_lower"], keep=keep)
    return df.drop(columns=["Title_lower"])


def mark_new_specs_rows(
    df: pd.DataFrame,
    old: pd.DataFrame | None = None,
    keep_existing_values: bool = True,
) -> pd.DataFrame:
    df = df.copy()
    if keep_existing_values and old is not None:
        require_columns(list(old.columns), [SPECS_TITLE_COLUMN], "existing cleaned specs")
        old_keys = set(old[SPECS_TITLE_COLUMN].str.lower())
        df["is_new"] = ~df[SPECS_TITLE_COLUMN].str.lower().isin(old_keys)
    else:
        df["is_new"] = True
    return df


def normalize_copilot_pc_column(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "Copilot+ PC" in df.columns:
        copilot = df["Copilot+ PC"]
        df["Copilot+ PC"] = np.where(
            copilot.map(lambda value: isinstance(value, bool)),
            copilot,
            copilot.astype("string").str.contains(r"\byes\b", case=False, na=False),
        )
    return df


def normalize_product_flag_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Gaming PC"] = df[SPECS_TITLE_COLUMN].str.contains("gaming laptop", case=False, na=False)
    if "AI features" in df.columns:
        df["AI features"] = df["AI features"].apply(clean_ai_feat)
    df["Product condition"] = df[SPECS_TITLE_COLUMN].apply(condition)
    if "Display type" in df.columns:
        df["Display type"] = df["Display type"].apply(bucket_display)
    return df


def normalize_port_count_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["USB Ports", "USB-C Ports"]:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int).astype("Int64")
    return df


def normalize_operating_system_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "Operating system" in df.columns:
        df["OS_norm"] = df["Operating system"].str.lower().str.strip()
        df["OS_norm"] = df["OS_norm"].replace({"macos sequioa": "macos sequoia"})
        df["Operating system"] = df["OS_norm"].apply(map_os)
        df["OS_family"] = df["Operating system"].apply(map_family)
    return df


def normalize_resolution_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "Monitor resolution" in df.columns:
        if "Resolution (Pixels)" in df.columns:
            merged_res = df["Monitor resolution"].fillna(df["Resolution (Pixels)"])
            df = df.drop(columns=["Resolution (Pixels)"])
        else:
            merged_res = df["Monitor resolution"]
        df["Monitor resolution"] = merged_res.apply(clean_resolution)
    return df


def normalize_processor_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "Processor Type" in df.columns:
        df["Processor Type"] = df["Processor Type"].apply(clean_processor_type)
        df["Processor brand"] = df["Processor Type"].apply(bucket_processor_brand)
    return df


def normalize_graphics_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "Graphics processor" in df.columns:
        df["Graphics processor"] = df.apply(get_gpu_bucket, axis=1)
        df["GPU brand"] = df["Graphics processor"].apply(bucket_gpu_brand)
    return df


def is_missing_value(value: object) -> bool:
    if pd.isna(value):
        return True
    return str(value).strip() == ""


def format_title_storage(amount: str, unit: str) -> str:
    number = float(amount)
    if number.is_integer():
        amount = str(int(number))
    else:
        amount = str(number).rstrip("0").rstrip(".")
    return f"{amount}{unit.upper()}"


def infer_display_size_from_title(title: object) -> object:
    match = TITLE_DISPLAY_SIZE_PATTERN.search(str(title))
    if not match:
        return pd.NA
    size = float(match.group(1))
    return int(size) if size.is_integer() else size


def infer_processor_from_title(title: object) -> object:
    text = str(title)
    for pattern, template in TITLE_PROCESSOR_PATTERNS:
        match = pattern.search(text)
        if match:
            return template.format(group1=match.group(1))
    return pd.NA


def infer_storage_from_title(title: object) -> object:
    text = str(title)
    match = TITLE_STORAGE_BRACKET_PATTERN.search(text)
    if match:
        storage = format_title_storage(match.group(1), match.group(2))
        return storage if storage in TITLE_STORAGE_ALLOWED_VALUES else pd.NA

    match = TITLE_STORAGE_SSD_PATTERN.search(text)
    if match:
        amount = match.group(1) or match.group(3)
        unit = match.group(2) or match.group(4)
        storage = format_title_storage(amount, unit)
        return storage if storage in TITLE_STORAGE_ALLOWED_VALUES else pd.NA

    return pd.NA


def apply_title_spec_fallbacks(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if SPECS_TITLE_COLUMN not in df.columns:
        return df

    if "Display size (inches)" in df.columns:
        inferred_display = df[SPECS_TITLE_COLUMN].apply(infer_display_size_from_title)
        mask = df["Display size (inches)"].map(is_missing_value) & inferred_display.notna()
        if mask.any():
            df["Display size (inches)"] = df["Display size (inches)"].astype("object")
            df.loc[mask, "Display size (inches)"] = inferred_display[mask]

    if "Processor Type" in df.columns:
        inferred_processor = df[SPECS_TITLE_COLUMN].apply(infer_processor_from_title)
        mask = df["Processor Type"].map(is_missing_value) & inferred_processor.notna()
        if mask.any():
            df.loc[mask, "Processor Type"] = inferred_processor[mask]

    inferred_storage = None
    for col in ["SSD storage", "Total Storage"]:
        if col in df.columns:
            if inferred_storage is None:
                inferred_storage = df[SPECS_TITLE_COLUMN].apply(infer_storage_from_title)
            mask = df[col].map(is_missing_value) & inferred_storage.notna()
            if mask.any():
                df.loc[mask, col] = inferred_storage[mask]

    return df


def preserve_existing_cleaned_values(df: pd.DataFrame, old: pd.DataFrame | None = None) -> pd.DataFrame:
    df = df.copy()
    if old is None:
        return df

    merged = df.merge(old, on=SPECS_TITLE_COLUMN, how="left", suffixes=("", "_old"))
    for col in df.columns:
        old_col = f"{col}_old"
        if old_col in merged.columns:
            merged[col] = merged[col].where(merged["is_new"], merged[old_col])
    return merged[df.columns]


def tag_discontinued_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    require_columns(list(df.columns), LISTING_CORE_COLUMNS, "historical listings")

    dates = df["DateCollected"].astype(str)
    dt_iso = pd.to_datetime(dates, format="%Y-%m-%d", errors="coerce")
    dt_eu = pd.to_datetime(dates, format="%d/%m/%Y", errors="coerce")
    df["DateCollected"] = dt_iso.fillna(dt_eu)

    latest_day = df["DateCollected"].max()
    last_seen = df.groupby("Link")["DateCollected"].max().reset_index()
    last_seen.rename(columns={"DateCollected": "Final appear day"}, inplace=True)

    df = df.merge(last_seen, on="Link", how="left")
    df["Discontinued"] = df["Final appear day"] < latest_day
    df["Price"] = parse_price_series(df["Price"])
    return df


def tag_discontinued_products(csv_file: str | Path, output_file: str | Path) -> Path:
    input_path = Path(csv_file)
    output_path = Path(output_file)
    df = pd.read_csv(input_path, encoding="utf-8-sig")
    df = tag_discontinued_dataframe(df)

    validate_tagged_listings_before_write(df)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Tagged file saved to: {output_path}")
    return output_path


def clean_ai_feat(value: object) -> object:
    text = str(value).lower()
    if "copilot" in text and "keyboard" in text:
        return "Copilot keyboard key"
    return np.nan


def condition(title: object) -> str:
    text = str(title).lower() if pd.notna(title) else ""
    if "renewed" in text:
        return "Renewed"
    if "refurbished" in text:
        return "Refurbished"
    return "Other"


def bucket_display(value: object) -> object:
    if pd.isna(value):
        return np.nan
    text = str(value).lower()
    if "liquid retina xdr" in text:
        return "Liquid Retina XDR"
    if text.strip() == "liquid retina":
        return "Liquid Retina"
    if "oled" in text:
        return "OLED"
    if "mini led" in text or "miniled" in text:
        return "Mini LED"
    if "ips" in text:
        return "IPS"
    if "tn" in text:
        return "TN"
    if "pixelsense" in text:
        return "PixelSense"
    if "led" in text or "lcd" in text:
        return "LCD/LED"
    if any(item in text for item in ["anti-glare", "sva", "uwva"]):
        return "Anti-glare/SVA"
    if "wva" in text:
        return "WVA"
    return "Other"


def map_os(os_str: object) -> str:
    if not isinstance(os_str, str):
        return "Other"
    if "chrome" in os_str:
        return "Chrome OS"
    if "windows 10 pro" in os_str:
        return "Windows 10 Pro"
    if "windows 10 home" in os_str:
        return "Windows 10 Home"
    if "windows 11 pro national academic" in os_str:
        return "Windows 11 Pro National Academic"
    if "windows 11 pro" in os_str:
        return "Windows 11 Pro"
    if "windows 11 home plus" in os_str:
        return "Windows 11 Home Plus"
    if "windows 11 home s" in os_str:
        return "Windows 11 Home S"
    if "windows 11 home" in os_str:
        return "Windows 11 Home"
    if re.match(r"windows 11(\s|$)", os_str):
        return "Windows 11"
    if "macos sequoia" in os_str:
        return "macOS Sequoia"
    if "macos ventura" in os_str:
        return "macOS Ventura"
    if "macos monterey" in os_str:
        return "macOS Monterey"
    if "macos sonoma" in os_str:
        return "macOS Sonoma"
    if "macos mojave" in os_str:
        return "macOS Mojave"
    if "macos catalina" in os_str:
        return "macOS Catalina"
    if "macos sierra" in os_str:
        return "macOS Sierra"
    if "macos big sur" in os_str:
        return "macOS Big Sur"
    if os_str == "macos":
        return "macOS"
    return "Other"


def map_family(os_clean: str) -> str:
    if os_clean.startswith("Windows"):
        return "Windows"
    if os_clean.startswith("macOS"):
        return "macOS"
    if os_clean == "Chrome OS":
        return "Chrome OS"
    return "Other"


def clean_resolution(raw: object) -> object:
    if pd.isna(raw):
        return pd.NA
    text = str(raw).strip().lower()
    text = re.sub(r"(\s*\*\s*|\s*-?by-?\s*|\s*\u00d7\s*)", "x", text)
    match = re.search(r"(\d{3,4})\s*x\s*(\d{3,4})", text)
    if not match:
        match = re.fullmatch(r"(\d{3,4})\s+(\d{3,4})", text)
    if not match:
        return pd.NA
    return f"{match.group(1)} x {match.group(2)}"


def clean_processor_type(raw: object) -> object:
    if pd.isna(raw):
        return pd.NA
    text = str(raw)
    text = re.sub(r"\u00ae|\u2122|\u00c2\u00ae|\u00e2\u201e\u00a2|\(.*?\)|\[.*?\]", "", text)
    text = re.sub(r"coretm", "Core", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def bucket_processor_brand(ptype: object) -> str:
    if isinstance(ptype, str):
        text = re.sub(r"\u00ae|\u2122|\u00c2\u00ae|\u00e2\u201e\u00a2|\(.*?\)|\[.*?\]", "", ptype.lower())
        if "intel" in text:
            return "Intel"
        if "qualcomm" in text:
            return "Qualcomm"
        if text.startswith("apple m"):
            return "Apple M"
        if text.startswith("apple a"):
            return "Apple A"
        if "ryzen" in text or "athlon" in text:
            return "AMD"
        if text.startswith("mtk"):
            return "MTK"
    return "Other"


def normalize_gpu_text(raw: object) -> str:
    text = str(raw).lower()
    text = re.sub(r"\u00ae|\u2122|(?<=[a-z])tm\b|\btm\b", "", text)
    return re.sub(r"\s+", " ", text).strip()


def infer_gpu_from_title(title: object) -> str | None:
    text = str(title)
    match = RTX_A_TITLE_PATTERN.search(text)
    if match:
        return f"NVIDIA RTX A{match.group(1)}"

    match = RTX_TITLE_PATTERN.search(text)
    if match:
        suffix = " Ti" if match.group(2) else ""
        return f"NVIDIA RTX {match.group(1)}{suffix}"

    return None


def get_gpu_bucket(row: pd.Series) -> str:
    if pd.isna(row.get("Graphics processor")) and not pd.isna(row.get("Graphics card series")):
        return row["Graphics card series"]

    title = str(row.get("Title", "")).lower()
    text = normalize_gpu_text(row.get("Graphics processor", ""))

    match = re.search(r"rtx[\s\-]?(\d{3,4}[ti]?)", text)
    if match:
        return f"NVIDIA RTX {match.group(1)}"
    match = re.search(r"geforce\s+(\d{3,4}[ti]?)", text)
    if match:
        return f"NVIDIA GeForce {match.group(1)}"
    if "iris" in text and "xe" in text:
        return "Intel Iris Xe"
    if "uhd" in text and "intel" in text:
        return "Intel UHD"
    if "hd graphics" in text or "intel hd" in text:
        return "Intel HD"
    if "pentium gold" in text:
        return "Intel Pentium Gold"
    if "arc" in text:
        return "Intel Arc"
    if "radeon" in text:
        return "AMD Radeon"
    if "adreno" in text:
        return "Qualcomm Adreno"
    if "mali" in text:
        return "ARM Mali"
    if "halo" in text:
        return "AMD Strix Halo"
    if "intel" in text and "graphic" in text:
        return "Intel Graphics"
    if "integrated" in text:
        return "Integrated"
    if re.search(r"\d+\s*core gpu", text) or "apple" in title:
        return "Apple GPU"
    inferred_gpu = infer_gpu_from_title(title)
    if inferred_gpu:
        return inferred_gpu
    return "Other"


def bucket_gpu_brand(raw: object) -> object:
    if pd.isna(raw):
        return pd.NA
    text = re.sub(r"®|™|\(.*?\)|\[.*?\]", "", str(raw).lower())
    if "intel" in text:
        return "Intel"
    if any(item in text for item in ("nvidia", "rtx", "gtx", "geforce")):
        return "NVIDIA"
    if any(item in text for item in ("amd", "radeon")):
        return "AMD"
    if "qualcomm" in text or "adreno" in text:
        return "Qualcomm"
    if "apple" in text:
        return "Apple"
    if "arm" in text or "mali" in text:
        return "ARM"
    if "integrated" in text:
        return "Integrated"
    return "Other"


def clean_specs_dataframe(
    df: pd.DataFrame,
    old: pd.DataFrame | None = None,
    keep_existing_values: bool = True,
) -> pd.DataFrame:
    df = df.copy()
    require_columns(list(df.columns), [SPECS_TITLE_COLUMN], "raw specs")
    df = dedupe_specs_by_title(df, keep="last")

    df = df.drop(columns=[col for col in DROP_SPEC_COLUMNS if col in df.columns])

    if keep_existing_values and old is not None:
        old = old.copy()

    df = mark_new_specs_rows(df, old=old, keep_existing_values=keep_existing_values)
    df = normalize_copilot_pc_column(df)
    df = normalize_product_flag_columns(df)
    df = normalize_port_count_columns(df)
    df = normalize_operating_system_columns(df)
    df = normalize_resolution_columns(df)
    df = apply_title_spec_fallbacks(df)
    df = normalize_processor_columns(df)
    df = normalize_graphics_columns(df)
    df = preserve_existing_cleaned_values(df, old=old)
    return df

def clean_specs(specs_file: str | Path, output_file: str | Path, keep_existing_values: bool = True) -> Path:
    """Clean raw specs.

    By default, existing cleaned values are preserved for previously seen titles.
    Set `keep_existing_values=False` to re-apply cleaning rules to every row.
    """
    specs_path = Path(specs_file)
    output_path = Path(output_file)

    df = pd.read_csv(specs_path, encoding="utf-8-sig")
    old = None
    if keep_existing_values and output_path.exists():
        old = pd.read_csv(output_path, encoding="utf-8-sig")

    df = clean_specs_dataframe(df, old=old, keep_existing_values=keep_existing_values)
    validate_clean_specs_before_write(df)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Cleaned specs saved to {output_path}")
    return output_path
