from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import csv
import time

# ------------------ Setup & Utilities ------------------ #
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode if desired
    return webdriver.Chrome(options=options)

def wait_for_element(driver, selector, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )

# ------------------ Scraping Functions ------------------ #
def load_all_products(driver):
    while True:
        try:
            load_more = driver.find_element(By.CLASS_NAME, "load-more-button")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more)
            time.sleep(1.5)
            load_more.click()
            time.sleep(2)
        except Exception:
            break  # Button no longer present — all products loaded

def extract_product_data(tile):
    try:
        title = tile.find_element(By.CSS_SELECTOR, "[data-testid='product-card-title']").text.strip()
        link = tile.find_element(By.CSS_SELECTOR, "a.ProductCard_imageLink").get_attribute("href")
        symbol = tile.find_element(By.CSS_SELECTOR, "span[class*='PriceTag_symbol']").text.strip()
        amount = tile.find_element(By.CSS_SELECTOR, "span[class*='PriceTag_actual']").text.strip()
        image = tile.find_element(By.CSS_SELECTOR, "img").get_attribute("src")
        price = f"{symbol}{amount}".strip()
        return [title, price, link, image]
    except NoSuchElementException:
        return None

# ------------------ Main Routine ------------------ #
def scrape_jbhifi_laptops(output_file="results.csv"):
    driver = setup_driver()
    driver.get("https://www.jbhifi.com.au/collections/computers-tablets/laptops?hitsPerPage=100")
    
    load_all_products(driver)
    product_tiles = driver.find_elements(By.CLASS_NAME, "ProductCard")

    print(f"🧠 Found {len(product_tiles)} products.")

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Title', 'Price', 'Link', 'ImageURL'])
        
        for tile in product_tiles:
            data = extract_product_data(tile)
            if data:
                writer.writerow(data)

    driver.quit()
    print(f"✅ Data saved to {output_file}!")

# ------------------ Run ------------------ #
if __name__ == "__main__":
    scrape_jbhifi_laptops()


def update_specs(core_file= "results.csv", specs_file="specs.csv", limit=None, delay=1, jitter=0.5):
    """
    Read results_core.csv to get Titles & Links.
    Read existing specs_file to skip already‐seen Titles.
    Fetch specs for new Titles, then rewrite specs_file
    with all Titles + complete set of spec columns.
    """
    # 1) load core data
    with open(core_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        core_rows = list(reader)

    # map Title -> Link
    title_to_link = {r["Title"]: r["Link"] for r in core_rows}

    # 2) load existing specs, if any
    existing = {}
    if os.path.exists(specs_file):
        with open(specs_file, newline='', encoding='utf-8') as f:
            rd = csv.DictReader(f)
            for r in rd:
                existing[r["Title"]] = {
                    k: v for k, v in r.items() if k not in ("Title",)
                }

    # 3) determine which Titles need specs fetched
    new_titles = [t for t in title_to_link if t not in existing]
    
    if limit:
        new_titles = new_titles[:limit]
    print(f"🛠️  Found {len(new_titles)} new laptops to fetch specs for.")

    # 4) fetch specs for new Titles
    for i, title in enumerate(new_titles, start=1):
        print(f"   • [{i}/{len(new_titles)}] Fetching specs for {title!r}")
        existing[title] = fetch_specs(title_to_link[title])
        specs = fetch_specs("https://www.jbhifi.com.au/products/asus-zenbook-a14-14-oled-laptop-copilot-pc512gb")
        print("    → fetch_specs returned:", specs or "(empty dict)")
        existing[title] = specs
        # pause before the next request
        wait = delay + random.random() * jitter
        time.sleep(wait)

    # 5) determine full spec columns across all entries
    all_spec_keys = set()
    for specs in existing.values():
        all_spec_keys.update(specs.keys())
    all_keys = sorted(all_spec_keys)

    # 6) rewrite specs CSV with header Title + spec_cols
    with open(specs_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(["Title"] + all_keys)

        for title, specs in existing.items():
            # normalize & unescape the title
            clean_title = unicodedata.normalize('NFKC', unescape(title))
            
            # prepare each column, normalize & unescape
            row_vals = []
            for key in all_keys:
                raw = specs.get(key, "")
                txt = ", ".join(map(str, raw)) if isinstance(raw, (list, tuple)) else str(raw)
                clean = unicodedata.normalize('NFKC', unescape(txt))
                row_vals.append(clean)
            
            writer.writerow([clean_title] + row_vals)

    print(f"✅ Specs data saved to {specs_file}")


# Delay time

