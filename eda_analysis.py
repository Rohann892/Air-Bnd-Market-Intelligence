import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style aesthetics
plt.style.use('ggplot')
sns.set_theme(style="darkgrid")
plt.rcParams.update({'font.sans-serif': 'Helvetica', 'axes.edgecolor': '#cccccc', 'axes.linewidth': 0.8})

def run_eda():
    print("--- Starting Exploratory Data Analysis (EDA) ---")
    data_path = 'airbnb_nyc_cleaned.csv'
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found. Running data pipeline first...")
        import data_pipeline
        data_pipeline.clean_and_transform()

    df = pd.read_csv(data_path)
    charts_dir = 'charts'
    os.makedirs(charts_dir, exist_ok=True)

    # 1. Correlation Matrix
    plt.figure(figsize=(10, 7))
    num_cols = ['price', 'rating', 'number_of_reviews', 'reviews_per_month', 'accommodates', 'minimum_nights', 'availability_365', 'calculated_host_listings_count']
    corr = df[num_cols].corr()
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap='Blues', linewidths=0.5, cbar_kws={"shrink": .8})
    plt.title('NYC Airbnb Numeric Features Correlation Matrix', fontsize=14, fontweight='bold', pad=15)
    plt.tight_layout()
    corr_chart = os.path.join(charts_dir, 'correlation_heatmap.png')
    plt.savefig(corr_chart, dpi=300)
    plt.close()
    print(f"Saved: {corr_chart}")

    # 2. Average Price by Borough & Room Type
    plt.figure(figsize=(12, 6))
    order = df.groupby('borough')['price'].mean().sort_values(ascending=False).index
    ax = sns.barplot(data=df, x='borough', y='price', hue='room_type', order=order, palette='viridis', ci=None)
    plt.title('Average Nightly Price ($) by Borough & Room Type', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Borough', fontsize=12, fontweight='bold')
    plt.ylabel('Average Price ($)', fontsize=12, fontweight='bold')
    plt.legend(title='Room Type', frameon=True)
    
    # Add values on top of bars
    for p in ax.patches:
        height = p.get_height()
        if not np.isnan(height) and height > 0:
            ax.annotate(f'${int(height)}', (p.get_x() + p.get_width() / 2., height / 2),
                        ha='center', va='center', fontsize=9, color='white', fontweight='bold', rotation=90)

    plt.tight_layout()
    price_chart = os.path.join(charts_dir, 'price_by_borough_roomtype.png')
    plt.savefig(price_chart, dpi=300)
    plt.close()
    print(f"Saved: {price_chart}")

    # 3. Superhosts vs Non-Superhosts Deep Dive
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Superhosts vs. Standard Hosts Performance Benchmarking', fontsize=16, fontweight='bold', y=0.98)

    palette = {'Superhost': '#ff385c', 'Standard Host': '#484848'}

    # Price Comparison
    sns.boxplot(ax=axes[0, 0], data=df, x='superhost_status', y='price', palette=palette, showfliers=False)
    axes[0, 0].set_title('Price ($) Distribution (Excl. Outliers)', fontweight='bold')
    axes[0, 0].set_xlabel('')
    axes[0, 0].set_ylabel('Nightly Price ($)')

    # Rating Comparison
    sns.kdeplot(ax=axes[0, 1], data=df, x='rating', hue='superhost_status', palette=palette, fill=True, common_norm=False, alpha=0.4)
    axes[0, 1].set_title('Review Rating Density Distribution', fontweight='bold')
    axes[0, 1].set_xlabel('Rating Score (out of 5.0)')

    # Review Count Comparison
    sns.barplot(ax=axes[1, 0], data=df, x='superhost_status', y='number_of_reviews', palette=palette, estimator=np.median, ci=None)
    axes[1, 0].set_title('Median Total Reviews Received', fontweight='bold')
    axes[1, 0].set_xlabel('')
    axes[1, 0].set_ylabel('Median Reviews')

    # Availability Comparison
    sns.barplot(ax=axes[1, 1], data=df, x='superhost_status', y='availability_365', palette=palette, estimator=np.mean, ci=None)
    axes[1, 1].set_title('Average Annual Days Available (365)', fontweight='bold')
    axes[1, 1].set_xlabel('')
    axes[1, 1].set_ylabel('Mean Available Days')

    plt.tight_layout()
    superhost_chart = os.path.join(charts_dir, 'superhost_performance_metrics.png')
    plt.savefig(superhost_chart, dpi=300)
    plt.close()
    print(f"Saved: {superhost_chart}")

    # 4. Rating vs Price Scatter Plot
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x='price', y='rating', hue='superhost_status', style='superhost_status', palette=palette, alpha=0.7, s=70)
    plt.title('Listing Rating vs. Nightly Price ($)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Nightly Price ($)', fontsize=12, fontweight='bold')
    plt.ylabel('Overall Rating', fontsize=12, fontweight='bold')
    plt.xlim(0, 1000)
    plt.ylim(3.0, 5.05)
    plt.tight_layout()
    scatter_chart = os.path.join(charts_dir, 'rating_vs_price_scatter.png')
    plt.savefig(scatter_chart, dpi=300)
    plt.close()
    print(f"Saved: {scatter_chart}")

    print("\n--- Key EDA Insights Summary ---")
    borough_stats = df.groupby('borough').agg(
        total_listings=('id', 'count'),
        avg_price=('price', 'mean'),
        avg_rating=('rating', 'mean'),
        total_reviews=('number_of_reviews', 'sum')
    ).round(2)
    print(borough_stats)

if __name__ == '__main__':
    run_eda()
