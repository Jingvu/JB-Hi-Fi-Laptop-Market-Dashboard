# JB-Hi-Fi Laptop Market Dashboard

### Summary
View the Dashboard (Updated Daily): https://app.powerbi.com/view?r=eyJrIjoiOWM1YzhiOTYtYjUwMS00ZWY4LThjMTItMGViNjc2OTkxYzcwIiwidCI6Ijc4NGU5YWE4LWI4ZjQtNGFhOS1iMTgzLTE5ODExNjE5YjllZSJ9

**Markets don’t stand still and neither should the data**

Worked in a laptop company, I know how critical it is to understand the market, not just for launching the right products, but for timing promotions and clearing aging stock. They are daily problems.

So, I built a Python scraper with daily refresh, cleaned and shaped it in Power Query, and modelled it in Power BI to answer one question:

💡 "In the daily price war for consumer attention, are we leading, matching, or chasing?" 💡

I broke it down into four angles:\
👉How is it shaped across price points and brands?\
👉Which technical specs dominate the shelf?\
👉What do ratings reveal?\
👉Where are the deepest discounts and are they worth it?

## Some Interesting Insights
- NVIDIA owns gaming GPUs, Intel risks irrelevance in this space\
Across the full range, Intel rules CPUs (51.7%) and leads GPU SKU count (29.8%). But in the gaming segment, it’s NVIDIA’s kingdom (93% GPU share) with Intel almost absent (2%) and CPUs in gaming still skew Intel (83%). With the RTX 50 series (Blackwell + GDDR7) grabbing headlines, past trends suggest a jump in demand for not just gaming rigs but also creator-ready and AI-capable models, potentially boosting NVIDIA’s SKU share and gaming ASPs.

- Apple proves strong branding can defy discount pressure\
With a ~$2.4K median price, minimal discounting (~9%), and strong SKU presence (29.8% of GPUs), Apple maintains top customer ratings without joining the price-cut race. This is the evidence that competing on discounts alone won’t dent a brand that’s ingrained in consumer identity and seen as worth paying full price for.

- Qualcomm’s potential\
Specs are converging on mobility and efficiency as the sweet spot (most common features: 16–32GB RAM, 14-inch displays, 1TB SSDs). Sitting at 15.3% SKU share and a ~$2.1K median price, Qualcomm’s Snapdragon X Elite/Plus now delivers x86-level performance, 15–20 hours of battery life and widening app compatibility. If consumers continue prioritizing portability over raw benchmark scores, ARM-powered laptops could win a bigger slice of the premium market.

## Key Features
### 1. Pricing Landscape
<img width="1423" height="800" alt="JB Hifi_Pricing" src="https://github.com/user-attachments/assets/5d29e8e5-0ea1-4df2-84f9-f98e5df40111" />


- Tracks the full SKU and median prices across laptop categories (Standard, Lightweight, Performance, Gaming).
- Identifies top/bottom priced products, brand price trends, and SKU concentration.
- Helps buyers and stakeholders benchmark pricing range and market spread.

### 2. Spec Dominance
<img width="1978" height="1125" alt="JB Hifi_Specs" src="https://github.com/user-attachments/assets/7f7b74ed-f05d-4823-bd45-28c7d86d3638" />


- Highlights dominant hardware specs: RAM tiers, SSD sizes, GPU/Processor popularity.
- Plots how these specs influence both price and market presence.
- Shows if premium specs (e.g. Apple M3, 2TB SSD) truly command higher prices.

### 3. Rating Momentum
<img width="1958" height="1125" alt="JB Hifi_Rating" src="https://github.com/user-attachments/assets/3bc91706-d7d0-407c-9303-29f70b3a039b" />


- Analyzes customer feedback across brands.
- Bubble quadrant compares median price vs. rating vs. brand presence.
- Tracks rating trends and model popularity shifts over time.

### 4. On-Sale Insights
<img width="1958" height="1125" alt="JB Hifi_Sale" src="https://github.com/user-attachments/assets/28a3586f-05d5-4e71-ab0e-4df47e4f2aac" />


- Focuses on discounts, with average/max % discount and product-specific deals.
- Visualizes which brands are most aggressive on markdowns.
- Includes price vs. rating bubble to reveal value-for-money deals.

## Data Pipeline Summary
This project covered the entire data lifecycle, from web scraping and governance to cleaning and Power BI visualization.

### 1. Data Collection & Scraping
- **Scraped product listings:** Used Selenium to extract laptop listings, prices, ratings, tags, and inferred brand names.
- **Fetched and merged technical specifications:** Pulled specs ìnormation from product pages, parsed JSON, and merged into the main dataset.
- **Data Governance & Management:** Saved daily scrapes, merged with duplication checks, auto-backed up, and validated schema and row counts.

### 2. Preprocessing & Data Cleaning (Python)
- **Initial Exploration:** Analyzed structure, data types, and distributions to guide cleaning and transformation.
- **Product Info Cleanup:** Standardized prices, cleaned text fields, flagged discontinued items, and dropped noise.
- **Technical Spec Cleanup:** Cleaned and bucketed specs, created flags, and ensured consistent formats across columns.

### 3. BI Integration (Power BI)
- **Final outputs:**\
    📁 results_tagged.csv → pricing, tags, brand, and lifecycle flags.\
    📁 results_specs_cleaned_all.csv → full product specs.
- Loaded into Power BI using Power Query, with additional transformations, grouping and calculations for dashboarding.

## How to Use
Click the link to explore the dashboard. Use filters and drill-downs to interact with different segments and discover trends.
