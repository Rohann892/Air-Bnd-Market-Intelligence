import pandas as pd
import numpy as np
import random
import os

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

NUM_LISTINGS = 1250

borough_neighborhoods = {
    'Manhattan': ['Midtown', 'East Village', 'Harlem', 'Chelsea', 'Upper West Side', 'SoHo', 'Greenwich Village', 'Hell\'s Kitchen', 'Tribeca', 'Financial District'],
    'Brooklyn': ['Williamsburg', 'Bushwick', 'Bedford-Stuyvesant', 'Crown Heights', 'DUMBO', 'Greenpoint', 'Park Slope', 'Brooklyn Heights', 'Cobble Hill'],
    'Queens': ['Astoria', 'Long Island City', 'Flushing', 'Sunnyside', 'Ridgewood', 'Forest Hills', 'Jackson Heights'],
    'Bronx': ['Mott Haven', 'Riverdale', 'Fordham', 'Pelham Bay', 'Concourse'],
    'Staten Island': ['St. George', 'Tompkinsville', 'Todt Hill', 'Stapleton']
}

borough_weights = [0.42, 0.36, 0.14, 0.05, 0.03]

borough_coords = {
    'Manhattan': (40.7831, -73.9712, 0.04),
    'Brooklyn': (40.6782, -73.9442, 0.05),
    'Queens': (40.7282, -73.7949, 0.06),
    'Bronx': (40.8448, -73.8648, 0.04),
    'Staten Island': (40.5795, -74.1502, 0.05)
}

room_types = ['Entire home/apt', 'Private room', 'Shared room', 'Hotel room']
room_type_weights = [0.52, 0.43, 0.03, 0.02]

adjectives = ['Cozy', 'Spacious', 'Modern', 'Luxury', 'Charming', 'Sunny', 'Quiet', 'Stunning', 'Chic', 'Rustic', 'Boho', 'Bright', 'Minimalist']
types_naming = ['Studio', 'Loft', 'Apartment', 'Suite', 'Room', 'Penthouse', 'Brownstone Unit', 'Haven', 'Retreat', 'Flat']

first_names = ['Alex', 'Sarah', 'Michael', 'Emma', 'David', 'Jessica', 'Daniel', 'Emily', 'James', 'Olivia', 'Carlos', 'Elena', 'Liam', 'Sophia', 'Benjamin', 'Mia', 'Noah', 'Ava', 'Ethan', 'Charlotte']

data = []

for i in range(1, NUM_LISTINGS + 1):
    listing_id = 10000 + i
    borough = np.random.choice(list(borough_neighborhoods.keys()), p=borough_weights)
    neighborhood = random.choice(borough_neighborhoods[borough])
    
    # Lat/Lng generation
    base_lat, base_lng, spread = borough_coords[borough]
    lat = round(base_lat + np.random.normal(0, spread/2), 5)
    lng = round(base_lng + np.random.normal(0, spread/2), 5)
    
    room_type = np.random.choice(room_types, p=room_type_weights)
    
    # Host attributes
    host_id = int(np.random.choice(range(1001, 1350)))
    host_name = random.choice(first_names)
    
    # Superhosts have better specs on average
    is_superhost = np.random.choice(['t', 'f'], p=[0.38, 0.62])
    
    # Accommodates
    if room_type in ['Shared room', 'Private room']:
        accommodates = int(np.random.choice([1, 2, 3], p=[0.4, 0.5, 0.1]))
    else:
        accommodates = int(np.random.choice([2, 3, 4, 5, 6, 8], p=[0.3, 0.25, 0.2, 0.1, 0.1, 0.05]))
    
    # Pricing logic based on borough and room type
    borough_base_price = {
        'Manhattan': 185,
        'Brooklyn': 125,
        'Queens': 85,
        'Bronx': 65,
        'Staten Island': 70
    }[borough]
    
    room_multiplier = {
        'Entire home/apt': 1.6,
        'Hotel room': 1.8,
        'Private room': 0.75,
        'Shared room': 0.4
    }[room_type]
    
    superhost_premium = 1.15 if is_superhost == 't' else 1.0
    
    noise = np.random.lognormal(0, 0.35)
    price = int(np.clip(borough_base_price * room_multiplier * superhost_premium * noise, 35, 950))
    
    # Reviews & Ratings
    if is_superhost == 't':
        number_of_reviews = int(np.random.gamma(shape=5, scale=12)) + 15
        rating = round(min(5.0, float(np.random.beta(45, 2) * 1.2 + 3.8)), 2)
    else:
        number_of_reviews = int(np.random.gamma(shape=2, scale=15))
        rating = round(min(5.0, float(np.random.beta(20, 4) * 1.5 + 3.2)), 2) if number_of_reviews > 0 else np.nan

    if number_of_reviews == 0:
        rating = np.nan
        reviews_per_month = np.nan
        last_review = None
    else:
        reviews_per_month = round(max(0.05, number_of_reviews / np.random.uniform(6, 36)), 2)
        days_ago = int(np.random.exponential(60))
        last_review = (pd.Timestamp('2026-08-01') - pd.Timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
    minimum_nights = int(np.random.choice([1, 2, 3, 4, 5, 7, 30], p=[0.3, 0.3, 0.15, 0.05, 0.05, 0.1, 0.05]))
    availability_365 = int(np.random.uniform(10, 350))
    calculated_host_listings_count = int(np.random.choice([1, 2, 3, 4, 8, 12], p=[0.65, 0.18, 0.08, 0.04, 0.03, 0.02]))
    
    name = f"{random.choice(adjectives)} {random.choice(types_naming)} in {neighborhood}"
    url = f"https://www.airbnb.com/rooms/{listing_id}"
    
    data.append({
        'id': listing_id,
        'name': name,
        'host_id': host_id,
        'host_name': host_name,
        'host_is_superhost': is_superhost,
        'borough': borough,
        'neighbourhood': neighborhood,
        'latitude': lat,
        'longitude': lng,
        'room_type': room_type,
        'price': price,
        'accommodates': accommodates,
        'minimum_nights': minimum_nights,
        'number_of_reviews': number_of_reviews,
        'last_review': last_review,
        'reviews_per_month': reviews_per_month,
        'calculated_host_listings_count': calculated_host_listings_count,
        'availability_365': availability_365,
        'rating': rating,
        'listing_url': url
    })

df = pd.DataFrame(data)

# Introduce a few intentional missing values / dirty formatting to demonstrate data cleaning step
# E.g. null host_name, whitespace in borough/room_type
df.loc[12, 'host_name'] = None
df.loc[45, 'borough'] = ' Manhattan '

df.to_csv('airbnb_nyc_listings.csv', index=False)
print(f"Dataset generated successfully with {len(df)} rows -> airbnb_nyc_listings.csv")
