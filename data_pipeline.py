import pandas as pd
import numpy as np
import json
import os

def clean_and_transform():
    print("--- Starting Data Cleaning & Transformation Pipeline ---")
    raw_path = 'airbnb_nyc_listings.csv'
    if not os.path.exists(raw_path):
        print(f"Error: {raw_path} does not exist. Run generate_dataset.py first.")
        return

    df = pd.read_csv(raw_path)
    initial_rows = len(df)
    print(f"Raw dataset loaded: {initial_rows} rows, {len(df.columns)} columns.")

    # Data Cleaning Steps
    # 1. Trim whitespace on text fields
    text_cols = ['name', 'host_name', 'borough', 'neighbourhood', 'room_type', 'host_is_superhost']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # 2. Handle missing values
    df['host_name'] = df['host_name'].replace('nan', 'Unknown Host').fillna('Unknown Host')
    df['reviews_per_month'] = df['reviews_per_month'].fillna(0.0)
    df['last_review'] = df['last_review'].replace('nan', 'No Reviews').fillna('No Reviews')
    
    # Impute missing ratings using borough + room_type median
    group_medians = df.groupby(['borough', 'room_type'])['rating'].transform('median')
    df['rating'] = df['rating'].fillna(group_medians).fillna(df['rating'].median()).round(2)

    # 3. Transformations & Feature Engineering
    # Price per person
    df['price_per_guest'] = (df['price'] / df['accommodates']).round(2)

    # Host Tiering
    def categorize_host(count):
        if count == 1:
            return 'Single Listing'
        elif count <= 4:
            return 'Small Host (2-4)'
        else:
            return 'Multi-Listing Host (5+)'

    df['host_tier'] = df['calculated_host_listings_count'].apply(categorize_host)

    # Price Tiering
    def categorize_price(price):
        if price < 100:
            return 'Budget (<$100)'
        elif price <= 250:
            return 'Moderate ($100-$250)'
        else:
            return 'Luxury (>$250)'

    df['price_category'] = df['price'].apply(categorize_price)

    # Superhost display label
    df['superhost_status'] = df['host_is_superhost'].apply(lambda x: 'Superhost' if str(x).lower() in ['t', 'true', '1'] else 'Standard Host')

    # Save cleaned CSV
    cleaned_csv = 'airbnb_nyc_cleaned.csv'
    df.to_csv(cleaned_csv, index=False)
    print(f"Cleaned dataset saved to {cleaned_csv}")

    # Export JSON for Web Dashboard
    records = df.to_dict(orient='records')
    json_path = 'dashboard_data.json'
    with open(json_path, 'w') as f:
        json.dump(records, f, indent=2)
    print(f"Exported JSON for web dashboard to {json_path}")

    # Summary Statistics Output
    print("\n--- Pipeline Summary ---")
    print(f"Total Listings: {len(df)}")
    print(f"Total Boroughs: {df['borough'].nunique()}")
    print(f"Superhosts: {len(df[df['superhost_status'] == 'Superhost'])} ({len(df[df['superhost_status'] == 'Superhost'])/len(df)*100:.1f}%)")
    print(f"Average Price: ${df['price'].mean():.2f}")
    print(f"Average Rating: {df['rating'].mean():.2f}")

if __name__ == '__main__':
    clean_and_transform()
