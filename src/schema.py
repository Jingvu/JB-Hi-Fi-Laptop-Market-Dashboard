LISTING_CORE_COLUMNS = [
    "DateCollected",
    "Brand",
    "Title",
    "Price",
    "FullPrice",
    "Link",
    "ImageURL",
    "Rating",
    "NumRating",
]

DAILY_APPEND_KEY_COLUMNS = ["DateCollected", "Title"]

SPECS_TITLE_COLUMN = "Title"


def missing_columns(columns: list[str], required_columns: list[str]) -> list[str]:
    return [column for column in required_columns if column not in columns]


def require_columns(columns: list[str], required_columns: list[str], dataset_name: str) -> None:
    missing = missing_columns(columns, required_columns)
    if missing:
        raise ValueError(f"{dataset_name} is missing required columns: {missing}")
