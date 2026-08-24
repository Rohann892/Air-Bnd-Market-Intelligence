import csv
import json
import random
import math
import datetime

# Set seed for reproducibility
random.seed(42)

NUM_LISTINGS = 1250

borough_neighborhoods = {
    'Manhattan': ['Midtown', 'East Village', 'Harlem', 'Chelsea', 'Upper West Side', 'SoHo', 'Greenwich Village', 'Hell\'s Kitchen', 'Tribeca', 'Financial District'],
    'Brooklyn': ['Williamsburg', 'Bushwick', 'Bedford-Stuyvesant', 'Crown Heights', 'DUMBO', 'Greenpoint', 'Park Slope', 'Brooklyn Heights', 'Cobble Hill'],
    'Queens': ['Astoria', 'Long Island City', 'Flushing', 'Sunnyside', 'Ridgewood', 'Forest Hills', 'Jackson Heights'],
    'Bronx': ['Mott Haven', 'Riverdale', 'Fordham', 'Pelham Bay', 'Concourse'],
    'Staten Island': ['St. George', 'Tompkinsville', 'Todt Hill', 'Stapleton']
}

borough_weights = [('Manhattan', 0.42), ('Brooklyn', 0.36), ('Queens', 0.14), ('Bronx', 0.05), ('Staten Island', 0.03)]

def weighted_choice(choices):
    total = sum(w for c, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices:
        if upto + w >= r:
            return c
        upto += w
    return choices[-1][0]

borough_coords = {
    'Manhattan': (40.7831, -73.9712, 0.04),
    'Brooklyn': (40.6782, -73.9442, 0.05),
    'Queens': (40.7282, -73.7949, 0.06),
    'Bronx': (40.8448, -73.8648, 0.04),
    'Staten Island': (40.5795, -74.1502, 0.05)
}

room_types = [('Entire home/apt', 0.52), ('Private room', 0.43), ('Shared room', 0.03), ('Hotel room', 0.02)]
adjectives = ['Cozy', 'Spacious', 'Modern', 'Luxury', 'Charming', 'Sunny', 'Quiet', 'Stunning', 'Chic', 'Rustic', 'Boho', 'Bright', 'Minimalist']
types_naming = ['Studio', 'Loft', 'Apartment', 'Suite', 'Room', 'Penthouse', 'Brownstone Unit', 'Haven', 'Retreat', 'Flat']
first_names = ['Alex', 'Sarah', 'Michael', 'Emma', 'David', 'Jessica', 'Daniel', 'Emily', 'James', 'Olivia', 'Carlos', 'Elena', 'Liam', 'Sophia', 'Benjamin', 'Mia', 'Noah', 'Ava', 'Ethan', 'Charlotte']

raw_rows = []
cleaned_rows = []

base_date = datetime.date(2026, 8, 1)

for i in range(1, NUM_LISTINGS + 1):
    listing_id = 10000 + i
    borough = weighted_choice(borough_weights)
    neighborhood = random.choice(borough_neighborhoods[borough])
    
    base_lat, base_lng, spread = borough_coords[borough]
    lat = round(base_lat + random.gauss(0, spread / 2), 5)
    lng = round(base_lng + random.gauss(0, spread / 2), 5)
    
    room_type = weighted_choice(room_types)
    host_id = random.randint(1001, 1350)
    host_name = random.choice(first_names)
    
    is_superhost = 't' if random.random() < 0.38 else 'f'
    superhost_status = 'Superhost' if is_superhost == 't' else 'Standard Host'
    
    if room_type in ['Shared room', 'Private room']:
        accommodates = weighted_choice([(1, 0.4), (2, 0.5), (3, 0.1)])
    else:
        accommodates = weighted_choice([(2, 0.3), (3, 0.25), (4, 0.2), (5, 0.1), (6, 0.1), (8, 0.05)])
        
    borough_base_price = {'Manhattan': 185, 'Brooklyn': 125, 'Queens': 85, 'Bronx': 65, 'Staten Island': 70}[borough]
    room_mult = {'Entire home/apt': 1.6, 'Hotel room': 1.8, 'Private room': 0.75, 'Shared room': 0.4}[room_type]
    superhost_prem = 1.15 if is_superhost == 't' else 1.0
    noise = math.exp(random.gauss(0, 0.35))
    price = max(35, min(950, int(borough_base_price * room_mult * superhost_prem * noise)))
    
    if is_superhost == 't':
        num_reviews = int(random.gammavariate(5, 12)) + 15
        rating = round(min(5.0, random.betavariate(45, 2) * 1.2 + 3.8), 2)
    else:
        num_reviews = int(random.gammavariate(2, 15))
        rating = round(min(5.0, random.betavariate(20, 4) * 1.5 + 3.2), 2) if num_reviews > 0 else 4.25

    if num_reviews == 0:
        reviews_per_month = 0.0
        last_review = 'No Reviews'
    else:
        reviews_per_month = round(max(0.05, num_reviews / random.uniform(6, 36)), 2)
        days_ago = int(random.expovariate(1/60))
        last_review = (base_date - datetime.timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
    minimum_nights = weighted_choice([(1, 0.3), (2, 0.3), (3, 0.15), (4, 0.05), (5, 0.05), (7, 0.1), (30, 0.05)])
    availability_365 = random.randint(10, 350)
    calculated_host_count = weighted_choice([(1, 0.65), (2, 0.18), (3, 0.08), (4, 0.04), (8, 0.03), (12, 0.02)])
    
    name = f"{random.choice(adjectives)} {random.choice(types_naming)} in {neighborhood}"
    url = f"https://www.airbnb.com/rooms/{listing_id}"
    
    # Host portfolio tier
    if calculated_host_count == 1:
        host_tier = 'Single Listing'
    elif calculated_host_count <= 4:
        host_tier = 'Small Host (2-4)'
    else:
        host_tier = 'Multi-Listing Host (5+)'
        
    # Price tier
    if price < 100:
        price_cat = 'Budget (<$100)'
    elif price <= 250:
        price_cat = 'Moderate ($100-$250)'
    else:
        price_cat = 'Luxury (>$250)'
        
    price_per_guest = round(price / accommodates, 2)
    
    item = {
        'id': listing_id,
        'name': name,
        'host_id': host_id,
        'host_name': host_name,
        'host_is_superhost': is_superhost,
        'superhost_status': superhost_status,
        'borough': borough,
        'neighbourhood': neighborhood,
        'latitude': lat,
        'longitude': lng,
        'room_type': room_type,
        'price': price,
        'accommodates': accommodates,
        'price_per_guest': price_per_guest,
        'minimum_nights': minimum_nights,
        'number_of_reviews': num_reviews,
        'last_review': last_review,
        'reviews_per_month': reviews_per_month,
        'calculated_host_listings_count': calculated_host_count,
        'host_tier': host_tier,
        'price_category': price_cat,
        'availability_365': availability_365,
        'rating': rating,
        'listing_url': url
    }
    
    cleaned_rows.append(item)

# Save Raw CSV
fieldnames = list(cleaned_rows[0].keys())
with open('airbnb_nyc_cleaned.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(cleaned_rows)

with open('airbnb_nyc_listings.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(cleaned_rows)

# Save Dashboard JSON
with open('dashboard_data.json', 'w') as f:
    json.dump(cleaned_rows, f, indent=2)

print(f"Standalone dataset pipeline executed successfully! Exported {len(cleaned_rows)} listings to airbnb_nyc_cleaned.csv and dashboard_data.json.")
