from __future__ import annotations

import csv
import re
import time
import warnings
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.common.by import By

from .schema import LISTING_CORE_COLUMNS


LAPTOPS_URL = "https://www.jbhifi.com.au/collections/computers-tablets/laptops?hitsPerPage=100"
MELBOURNE_TZ = ZoneInfo("Australia/Melbourne")

# These selectors depend on JB Hi-Fi's storefront markup and may break after a site redesign.
LOAD_MORE_BUTTON_CLASS = "load-more-button"
PRODUCT_CARD_CLASS = "ProductCard"
PRODUCT_TITLE_SELECTOR = "[data-testid='product-card-title']"
PRODUCT_LINK_SELECTOR = "a.ProductCard_imageLink"
PRICE_SYMBOL_SELECTOR = "span[class*='PriceTag_symbol']"
PRICE_AMOUNT_SELECTOR = "span[class*='PriceTag_actual']"
PRODUCT_IMAGE_SELECTOR = "img"
FULL_PRICE_SELECTOR = "span[class*='PriceTag_symbolHeader'] + span"
RATING_SELECTOR = "[data-testid='product-card-reviews'] button._6zw1gn1 ._6zw1gna"
RATING_COUNT_SELECTOR = "div[class*='_6zw1gnb']"
PROMO_TAG_SELECTOR = (
    "span[data-testid='product-card-banner-tag'], "
    "span[data-testid^='product-card-promo-tag-']"
)

REQUIRED_SCRAPED_ROW_FIELDS = ("date", "title", "price", "fullprice", "link", "image", "tags")


def setup_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    return webdriver.Chrome(options=options)


def load_all_products(driver: webdriver.Chrome, scroll_pause: float = 1, click_pause: float = 2) -> None:
    while True:
        try:
            button = driver.find_element(By.CLASS_NAME, LOAD_MORE_BUTTON_CLASS)
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(scroll_pause)
            try:
                button.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", button)
            time.sleep(click_pause)
        except NoSuchElementException:
            break


def extract_brand(title: str) -> str:
    brands = [
        "HP", "ASUS", "Dell", "Apple", "Lenovo", "MSI", "Acer", "Alienware",
        "Gigabyte", "Erazer", "Microsoft", "Samsung", "Leader", "LG", 
        "Aftershock", "HyperX"
    ]
    title_lower = title.lower()
    for brand in brands:
        if brand.lower() in title_lower:
            return brand
    if "lg gram" in title_lower:
        return "LG"
    if "lenvo" in title_lower:
        return "Lenovo"
    if "victus" in title_lower:
        return "HP"
    if "proart" in title_lower: 
        return "ASUS"
    if "omen" in title_lower:
        return "HP"
    return "Other"


def extract_product_data(tile) -> dict[str, object] | None:
    date_collected = datetime.now(MELBOURNE_TZ).date().isoformat()
    try:
        title = tile.find_element(By.CSS_SELECTOR, PRODUCT_TITLE_SELECTOR).text.strip()
        link = tile.find_element(By.CSS_SELECTOR, PRODUCT_LINK_SELECTOR).get_attribute("href")
        symbol = tile.find_element(By.CSS_SELECTOR, PRICE_SYMBOL_SELECTOR).text.strip()
        amount = tile.find_element(By.CSS_SELECTOR, PRICE_AMOUNT_SELECTOR).text.strip()
        image = tile.find_element(By.CSS_SELECTOR, PRODUCT_IMAGE_SELECTOR).get_attribute("src")
        price = f"{symbol}{amount}".strip() if amount else "N/A"

        try:
            fullprice = tile.find_element(
                By.CSS_SELECTOR,
                FULL_PRICE_SELECTOR,
            ).text.strip()
            fullprice = f"{symbol}{fullprice}"
        except NoSuchElementException:
            fullprice = price

        try:
            rating_txt = tile.find_element(
                By.CSS_SELECTOR,
                RATING_SELECTOR,
            ).text.strip()
            rating = float(rating_txt)
        except Exception:
            rating = None

        try:
            num_txt = tile.find_element(By.CSS_SELECTOR, RATING_COUNT_SELECTOR).text.strip()
            num_ratings = int(re.sub(r"\D", "", num_txt))
        except (NoSuchElementException, ValueError):
            num_ratings = None

        tag_spans = tile.find_elements(
            By.CSS_SELECTOR,
            PROMO_TAG_SELECTOR,
        )
        tags = [tag.text.strip() for tag in tag_spans if tag.text.strip()]

        return {
            "date": date_collected,
            "title": title,
            "price": price,
            "fullprice": fullprice,
            "link": link,
            "image": image,
            "rating": rating,
            "num_ratings": num_ratings,
            "tags": tags,
        }
    except NoSuchElementException:
        return None


def validate_scraped_rows(rows: list[dict[str, object]], min_rows: int = 1) -> list[str]:
    issues: list[str] = []
    if len(rows) < min_rows:
        issues.append(f"Expected at least {min_rows} scraped rows, found {len(rows)}.")

    for index, row in enumerate(rows, start=1):
        missing = [field for field in REQUIRED_SCRAPED_ROW_FIELDS if field not in row]
        if missing:
            issues.append(f"Row {index} is missing required fields: {missing}.")
        if "tags" in row and not isinstance(row["tags"], list):
            issues.append(f"Row {index} has non-list tags: {type(row['tags']).__name__}.")

    return issues


def validate_scraped_rows_before_write(rows: list[dict[str, object]]) -> None:
    issues = validate_scraped_rows(rows, min_rows=1)
    unsafe = [
        issue for issue in issues
        if "missing required fields" in issue or "non-list tags" in issue
    ]
    if unsafe:
        raise ValueError(f"Scraped rows are not safe to write: {unsafe}")
    for issue in issues:
        warnings.warn(issue, RuntimeWarning, stacklevel=2)


def extract_product_rows(cards, extractor=extract_product_data) -> tuple[list[dict[str, object]], int]:
    rows = []
    skipped_count = 0
    for card in cards:
        row = extractor(card)
        if row:
            rows.append(row)
        else:
            skipped_count += 1
    return rows, skipped_count


def scrape_jbhifi_laptops(output_file: str | Path) -> Path:
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    driver = setup_driver()
    try:
        driver.get(LAPTOPS_URL)
        load_all_products(driver)
        cards = driver.find_elements(By.CLASS_NAME, PRODUCT_CARD_CLASS)
        print(f"Found {len(cards)} products.")
        rows, skipped_count = extract_product_rows(cards)
        if skipped_count:
            warnings.warn(
                f"Skipped {skipped_count} product cards because required fields were missing.",
                RuntimeWarning,
                stacklevel=2,
            )
    finally:
        driver.quit()

    max_tags = max((len(row["tags"]) for row in rows), default=0)
    tag_cols = [f"Tag{i + 1}" for i in range(max_tags)]

    validate_scraped_rows_before_write(rows)
    with output_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(LISTING_CORE_COLUMNS + tag_cols)
        for row in rows:
            core_vals = [
                row["date"],
                extract_brand(str(row["title"])),
                row["title"],
                row["price"],
                row["fullprice"],
                row["link"],
                row["image"],
                row["rating"],
                row["num_ratings"],
            ]
            padded_tags = row["tags"] + [""] * (max_tags - len(row["tags"]))
            writer.writerow(core_vals + padded_tags)

    print(f"Data saved to {output_path}")
    return output_path
