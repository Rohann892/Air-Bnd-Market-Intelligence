-- ===============================================================================
-- NYC AIRBNB DATA ANALYTICS & INSIGHTS QUERY SUITE
-- Target System: SQL Server Management Studio (SSMS) / T-SQL / ANSI SQL standard
-- Author: Data Analytics Team
-- Description: Complete SQL analysis suite including CTEs, Self-Joins, Window Functions, 
--              Data Cleaning DDL, Stored Procedures, and Superhost Edge Benchmarking.
-- ===============================================================================

USE AirbnbNYC;
GO

-- -------------------------------------------------------------------------------
-- SECTION 1: DATA CLEANING & TRANSFORMATION VIEW
-- -------------------------------------------------------------------------------

CREATE OR ALTER VIEW dbo.vw_Airbnb_Listings_Cleaned AS
SELECT 
    id AS listing_id,
    LTRIM(RTRIM(name)) AS listing_name,
    host_id,
    ISNULL(NULLIF(LTRIM(RTRIM(host_name)), ''), 'Unknown Host') AS host_name,
    CASE 
        WHEN LOWER(host_is_superhost) IN ('t', 'true', '1') THEN 'Superhost'
        ELSE 'Standard Host'
    END AS superhost_status,
    LTRIM(RTRIM(borough)) AS borough,
    LTRIM(RTRIM(neighbourhood)) AS neighbourhood,
    latitude,
    longitude,
    room_type,
    price,
    accommodates,
    ROUND(CAST(price AS FLOAT) / NULLIF(accommodates, 0), 2) AS price_per_guest,
    minimum_nights,
    number_of_reviews,
    ISNULL(reviews_per_month, 0.0) AS reviews_per_month,
    calculated_host_listings_count,
    CASE 
        WHEN calculated_host_listings_count = 1 THEN 'Single Listing Host'
        WHEN calculated_host_listings_count BETWEEN 2 AND 4 THEN 'Small Portfolio (2-4)'
        ELSE 'Commercial Portfolio (5+)'
    END AS host_portfolio_tier,
    availability_365,
    ISNULL(rating, 4.50) AS rating,
    listing_url
FROM dbo.raw_airbnb_nyc_listings;
GO

-- -------------------------------------------------------------------------------
-- SECTION 2: OVERVIEW & BOROUGH METRICS (USING CTEs & GROUP BY)
-- -------------------------------------------------------------------------------

-- Q1: Borough Summary Metrics for Dashboard Visualizations
WITH BoroughStats AS (
    SELECT 
        borough,
        COUNT(listing_id) AS total_listings,
        SUM(accommodates) AS total_accommodations_available,
        AVG(CAST(price AS DECIMAL(10,2))) AS avg_price_usd,
        AVG(CAST(rating AS DECIMAL(10,2))) AS avg_rating,
        SUM(number_of_reviews) AS total_reviews,
        SUM(CASE WHEN superhost_status = 'Superhost' THEN 1 ELSE 0 END) AS superhost_count
    FROM dbo.vw_Airbnb_Listings_Cleaned
    GROUP BY borough
)
SELECT 
    borough,
    total_listings,
    total_accommodations_available,
    ROUND(avg_price_usd, 2) AS avg_price_usd,
    ROUND(avg_rating, 2) AS avg_rating,
    total_reviews,
    superhost_count,
    ROUND(CAST(superhost_count AS FLOAT) / total_listings * 100, 2) AS superhost_pct
FROM BoroughStats
ORDER BY avg_price_usd DESC;
GO

-- -------------------------------------------------------------------------------
-- SECTION 3: SUPERHOST VS STANDARD HOST BENCHMARKING (THE SUPERHOST EDGE)
-- -------------------------------------------------------------------------------

-- Q2: Superhost Competitive Edge (Pricing Power, Review Volume & Occupancy Metric)
WITH SuperhostMetrics AS (
    SELECT 
        superhost_status,
        room_type,
        COUNT(listing_id) AS total_units,
        ROUND(AVG(CAST(price AS DECIMAL(10,2))), 2) AS avg_nightly_price,
        ROUND(AVG(CAST(rating AS DECIMAL(10,2))), 2) AS avg_rating_score,
        ROUND(AVG(CAST(number_of_reviews AS DECIMAL(10,2))), 2) AS avg_reviews_per_listing,
        ROUND(AVG(CAST(availability_365 AS DECIMAL(10,2))), 2) AS avg_annual_availability_days
    FROM dbo.vw_Airbnb_Listings_Cleaned
    GROUP BY superhost_status, room_type
)
SELECT 
    room_type,
    MAX(CASE WHEN superhost_status = 'Superhost' THEN avg_nightly_price END) AS superhost_avg_price,
    MAX(CASE WHEN superhost_status = 'Standard Host' THEN avg_nightly_price END) AS standard_avg_price,
    ROUND(MAX(CASE WHEN superhost_status = 'Superhost' THEN avg_nightly_price END) - 
          MAX(CASE WHEN superhost_status = 'Standard Host' THEN avg_nightly_price END), 2) AS superhost_price_premium,
    MAX(CASE WHEN superhost_status = 'Superhost' THEN avg_rating_score END) AS superhost_rating,
    MAX(CASE WHEN superhost_status = 'Standard Host' THEN avg_rating_score END) AS standard_rating,
    MAX(CASE WHEN superhost_status = 'Superhost' THEN avg_reviews_per_listing END) AS superhost_avg_reviews,
    MAX(CASE WHEN superhost_status = 'Standard Host' THEN avg_reviews_per_listing END) AS standard_avg_reviews
FROM SuperhostMetrics
GROUP BY room_type
ORDER BY superhost_price_premium DESC;
GO

-- -------------------------------------------------------------------------------
-- SECTION 4: MULTI-LISTING HOST ANALYSIS (USING SELF-JOINS)
-- -------------------------------------------------------------------------------

-- Q3: Self-Join to Compare Host Multi-Property Strategy across Boroughs
SELECT 
    h1.host_id,
    h1.host_name,
    h1.borough AS primary_borough,
    h1.listing_name AS listing_1_name,
    h1.price AS listing_1_price,
    h2.borough AS secondary_borough,
    h2.listing_name AS listing_2_name,
    h2.price AS listing_2_price,
    ABS(h1.price - h2.price) AS price_delta
FROM dbo.vw_Airbnb_Listings_Cleaned h1
INNER JOIN dbo.vw_Airbnb_Listings_Cleaned h2 
    ON h1.host_id = h2.host_id 
    AND h1.listing_id < h2.listing_id
WHERE h1.calculated_host_listings_count > 1
ORDER BY price_delta DESC;
GO

-- -------------------------------------------------------------------------------
-- SECTION 5: WINDOW FUNCTIONS & PERCENTILE RANKINGS
-- -------------------------------------------------------------------------------

-- Q4: Rank Top Listings per Borough by Rating and Reviews
WITH RankedListings AS (
    SELECT 
        listing_id,
        listing_name,
        borough,
        neighbourhood,
        room_type,
        price,
        rating,
        number_of_reviews,
        DENSE_RANK() OVER (PARTITION BY borough ORDER BY rating DESC, number_of_reviews DESC) AS rank_in_borough,
        NTILE(4) OVER (PARTITION BY borough ORDER BY price ASC) AS price_quartile
    FROM dbo.vw_Airbnb_Listings_Cleaned
)
SELECT * 
FROM RankedListings
WHERE rank_in_borough <= 5
ORDER BY borough, rank_in_borough;
GO

-- -------------------------------------------------------------------------------
-- SECTION 6: STORED PROCEDURE FOR DYNAMIC FILTERING & REVENUE POTENTIAL
-- -------------------------------------------------------------------------------

CREATE OR ALTER PROCEDURE dbo.sp_SearchAirbnbListings
    @TargetBorough VARCHAR(50) = NULL,
    @TargetRoomType VARCHAR(50) = NULL,
    @MaxPrice INT = 1000,
    @MinRating DECIMAL(3,2) = 4.0,
    @SuperhostOnly BIT = 0
AS
BEGIN
    SET NOCOUNT ON;

    SELECT 
        listing_id,
        listing_name,
        host_name,
        superhost_status,
        borough,
        neighbourhood,
        room_type,
        price,
        accommodates,
        rating,
        number_of_reviews,
        -- Estimated annual revenue proxy: (365 - availability) * price
        (365 - availability_365) * price AS estimated_annual_revenue_usd,
        listing_url
    FROM dbo.vw_Airbnb_Listings_Cleaned
    WHERE (@TargetBorough IS NULL OR borough = @TargetBorough)
      AND (@TargetRoomType IS NULL OR room_type = @TargetRoomType)
      AND price <= @MaxPrice
      AND rating >= @MinRating
      AND (@SuperhostOnly = 0 OR superhost_status = 'Superhost')
    ORDER BY rating DESC, number_of_reviews DESC;
END;
GO
