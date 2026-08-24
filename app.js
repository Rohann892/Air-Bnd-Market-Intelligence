// NYC AIRBNB DASHBOARD - APPLICATION JAVASCRIPT LOGIC

let rawListingsData = [];
let filteredData = [];
let leafletMap = null;
let mapMarkersGroup = null;

// Chart.js Instances
let chartBoroughPriceInst = null;
let chartRoomTypeInst = null;
let chartSuperhostBenchmarkInst = null;
let chartRatingScatterInst = null;

// SQL Presets Map
const sqlPresets = {
  q1: `-- 1. Borough Summary Metrics (Group By & Aggregation)
SELECT 
    borough,
    COUNT(id) AS total_listings,
    SUM(accommodates) AS total_accommodations,
    ROUND(AVG(price), 2) AS avg_price_usd,
    ROUND(AVG(rating), 2) AS avg_rating,
    SUM(number_of_reviews) AS total_reviews,
    ROUND(COUNT(CASE WHEN host_is_superhost = 't' THEN 1 END) * 100.0 / COUNT(id), 1) AS superhost_pct
FROM airbnb
GROUP BY borough
ORDER BY avg_price_usd DESC;`,

  q2: `-- 2. Superhost Competitive Edge (Price & Rating Delta)
SELECT 
    superhost_status,
    COUNT(id) AS total_units,
    ROUND(AVG(price), 2) AS avg_price,
    ROUND(AVG(rating), 2) AS avg_rating,
    ROUND(AVG(number_of_reviews), 1) AS avg_reviews_received,
    ROUND(AVG(availability_365), 0) AS avg_annual_days_available
FROM airbnb
GROUP BY superhost_status;`,

  q3: `-- 3. Multi-Listing Host Portfolio Analysis
SELECT 
    host_tier,
    COUNT(id) AS total_listings,
    ROUND(AVG(price), 2) AS avg_price,
    ROUND(AVG(rating), 2) AS avg_rating
FROM airbnb
GROUP BY host_tier
ORDER BY total_listings DESC;`,

  q4: `-- 4. Top 5 Highest Rated Listings per Borough
SELECT 
    id,
    name,
    borough,
    neighbourhood,
    room_type,
    price,
    rating,
    number_of_reviews
FROM airbnb
WHERE rating >= 4.8 AND number_of_reviews >= 30
ORDER BY rating DESC, number_of_reviews DESC
LIMIT 10;`,

  q5: `-- 5. High Value Luxury Listings (>$300/night)
SELECT 
    id,
    name,
    borough,
    room_type,
    price,
    rating,
    superhost_status,
    listing_url
FROM airbnb
WHERE price > 300
ORDER BY price DESC
LIMIT 15;`
};

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initFilterControls();
  initSQLEditor();
  loadData();
});

// 1. Navigation Tab Switching
function initTabs() {
  const tabBtns = document.querySelectorAll('.nav-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const targetId = btn.getAttribute('data-tab');
      document.getElementById(targetId).classList.add('active');

      if (targetId === 'tab-map' && leafletMap) {
        setTimeout(() => { leafletMap.invalidateSize(); }, 200);
      }
    });
  });
}

// 2. Fetch and Load Dataset
async function loadData() {
  try {
    const res = await fetch('dashboard_data.json');
    if (res.ok) {
      rawListingsData = await res.json();
    } else {
      throw new Error("JSON file not found");
    }
  } catch (err) {
    console.warn("Loading fallback sample data...", err);
    rawListingsData = generateFallbackData();
  }

  // Register table in AlaSQL for live query runner
  if (window.alasql) {
    alasql('CREATE TABLE IF NOT EXISTS airbnb');
    alasql('DELETE FROM airbnb');
    alasql.tables.airbnb.data = rawListingsData;
  }

  filteredData = [...rawListingsData];
  
  updateDashboard();
  initMap();
  populateLeaderboard();
  
  // Set default query in SQL editor
  document.getElementById('sqlQueryText').value = sqlPresets['q1'];
  runSQLQuery();
}

// 3. Filter Controls Handler
function initFilterControls() {
  const boroughSel = document.getElementById('filterBorough');
  const roomTypeSel = document.getElementById('filterRoomType');
  const superhostSel = document.getElementById('filterSuperhost');
  const priceSlider = document.getElementById('filterPrice');
  const priceValDisp = document.getElementById('priceValue');
  const searchInput = document.getElementById('filterSearch');
  const btnReset = document.getElementById('btnResetFilters');

  priceSlider.addEventListener('input', (e) => {
    priceValDisp.textContent = `$${e.target.value}`;
    applyFilters();
  });

  [boroughSel, roomTypeSel, superhostSel, searchInput].forEach(elem => {
    elem.addEventListener('input', applyFilters);
  });

  btnReset.addEventListener('click', () => {
    boroughSel.value = 'All';
    roomTypeSel.value = 'All';
    superhostSel.value = 'All';
    priceSlider.value = 1000;
    priceValDisp.textContent = '$1000';
    searchInput.value = '';
    applyFilters();
  });
}

function applyFilters() {
  const borough = document.getElementById('filterBorough').value;
  const roomType = document.getElementById('filterRoomType').value;
  const superhost = document.getElementById('filterSuperhost').value;
  const maxPrice = parseFloat(document.getElementById('filterPrice').value);
  const searchStr = document.getElementById('filterSearch').value.toLowerCase().trim();

  filteredData = rawListingsData.filter(d => {
    if (borough !== 'All' && d.borough !== borough) return false;
    if (roomType !== 'All' && d.room_type !== roomType) return false;
    if (superhost !== 'All' && d.superhost_status !== superhost) return false;
    if (d.price > maxPrice) return false;
    if (searchStr.length > 0) {
      const matchName = d.name.toLowerCase().includes(searchStr);
      const matchNeigh = d.neighbourhood.toLowerCase().includes(searchStr);
      const matchHost = (d.host_name || '').toLowerCase().includes(searchStr);
      if (!matchName && !matchNeigh && !matchHost) return false;
    }
    return true;
  });

  updateDashboard();
  updateMapMarkers();
}

// 4. Update KPI Metrics & Charts
function updateDashboard() {
  const totalListings = filteredData.length;
  const totalAccommodations = filteredData.reduce((acc, cur) => acc + (cur.accommodates || 0), 0);
  const avgPrice = totalListings > 0 ? (filteredData.reduce((acc, cur) => acc + cur.price, 0) / totalListings).toFixed(2) : 0;
  const avgRating = totalListings > 0 ? (filteredData.reduce((acc, cur) => acc + (cur.rating || 0), 0) / totalListings).toFixed(2) : 0;
  const totalReviews = filteredData.reduce((acc, cur) => acc + (cur.number_of_reviews || 0), 0);
  
  const superhosts = filteredData.filter(d => d.superhost_status === 'Superhost');
  const superhostCount = superhosts.length;
  const superhostPct = totalListings > 0 ? ((superhostCount / totalListings) * 100).toFixed(1) : 0;

  // KPI UI
  document.getElementById('kpiListings').textContent = totalListings.toLocaleString();
  document.getElementById('kpiAccommodations').textContent = totalAccommodations.toLocaleString();
  document.getElementById('kpiAvgPrice').textContent = `$${avgPrice}`;
  document.getElementById('kpiAvgRating').textContent = `${avgRating} ★`;
  document.getElementById('kpiTotalReviews').textContent = `${totalReviews.toLocaleString()} Total Reviews`;
  document.getElementById('kpiSuperhostPct').textContent = `${superhostPct}%`;
  document.getElementById('kpiSuperhostCount').textContent = `${superhostCount} Superhosts`;

  // Render Charts
  renderChartBoroughPrice();
  renderChartRoomType();
  renderChartSuperhostBenchmark();
  renderChartRatingScatter();
}

// 5. Chart Renderers
function renderChartBoroughPrice() {
  const ctx = document.getElementById('chartBoroughPrice').getContext('2d');
  
  const boroughs = ['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island'];
  const avgPrices = boroughs.map(b => {
    const items = filteredData.filter(d => d.borough === b);
    return items.length ? (items.reduce((a, c) => a + c.price, 0) / items.length).toFixed(2) : 0;
  });

  if (chartBoroughPriceInst) chartBoroughPriceInst.destroy();

  chartBoroughPriceInst = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: boroughs,
      datasets: [{
        label: 'Avg Nightly Price ($)',
        data: avgPrices,
        backgroundColor: ['#ff385c', '#38bdf8', '#a855f7', '#10b981', '#f59e0b'],
        borderRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
        x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
      }
    }
  });
}

function renderChartRoomType() {
  const ctx = document.getElementById('chartRoomType').getContext('2d');
  
  const roomTypes = ['Entire home/apt', 'Private room', 'Shared room', 'Hotel room'];
  const counts = roomTypes.map(rt => filteredData.filter(d => d.room_type === rt).length);

  if (chartRoomTypeInst) chartRoomTypeInst.destroy();

  chartRoomTypeInst = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: roomTypes,
      datasets: [{
        data: counts,
        backgroundColor: ['#a855f7', '#38bdf8', '#10b981', '#f59e0b'],
        borderWidth: 2,
        borderColor: '#0f172a'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right', labels: { color: '#f8fafc', font: { size: 11 } } }
      }
    }
  });
}

function renderChartSuperhostBenchmark() {
  const ctx = document.getElementById('chartSuperhostBenchmark').getContext('2d');

  const sh = filteredData.filter(d => d.superhost_status === 'Superhost');
  const std = filteredData.filter(d => d.superhost_status === 'Standard Host');

  const shPrice = sh.length ? (sh.reduce((a,c)=>a+c.price,0)/sh.length).toFixed(1) : 0;
  const stdPrice = std.length ? (std.reduce((a,c)=>a+c.price,0)/std.length).toFixed(1) : 0;

  const shRating = sh.length ? (sh.reduce((a,c)=>a+(c.rating||0),0)/sh.length * 20).toFixed(1) : 0; // scaled for bar
  const stdRating = std.length ? (std.reduce((a,c)=>a+(c.rating||0),0)/std.length * 20).toFixed(1) : 0;

  const shReviews = sh.length ? (sh.reduce((a,c)=>a+c.number_of_reviews,0)/sh.length).toFixed(1) : 0;
  const stdReviews = std.length ? (std.reduce((a,c)=>a+c.number_of_reviews,0)/std.length).toFixed(1) : 0;

  if (chartSuperhostBenchmarkInst) chartSuperhostBenchmarkInst.destroy();

  chartSuperhostBenchmarkInst = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Avg Price ($)', 'Rating Score (x20)', 'Avg Review Volume'],
      datasets: [
        { label: 'Superhosts', data: [shPrice, shRating, shReviews], backgroundColor: '#ff385c', borderRadius: 6 },
        { label: 'Standard Hosts', data: [stdPrice, stdRating, stdReviews], backgroundColor: '#475569', borderRadius: 6 }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#f8fafc' } } },
      scales: {
        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
        x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
      }
    }
  });
}

function renderChartRatingScatter() {
  const ctx = document.getElementById('chartRatingScatter').getContext('2d');

  // Sample max 150 points for scatter performance
  const sample = filteredData.slice(0, 150).map(d => ({
    x: d.price,
    y: d.rating,
    isSuperhost: d.superhost_status === 'Superhost'
  }));

  const shPoints = sample.filter(p => p.isSuperhost);
  const stdPoints = sample.filter(p => !p.isSuperhost);

  if (chartRatingScatterInst) chartRatingScatterInst.destroy();

  chartRatingScatterInst = new Chart(ctx, {
    type: 'scatter',
    data: {
      datasets: [
        { label: 'Superhost', data: shPoints, backgroundColor: '#ff385c', pointRadius: 5 },
        { label: 'Standard Host', data: stdPoints, backgroundColor: '#38bdf8', pointRadius: 4 }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#f8fafc' } } },
      scales: {
        x: { title: { display: true, text: 'Price ($)', color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
        y: { title: { display: true, text: 'Rating Score', color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' }, min: 3.0, max: 5.0 }
      }
    }
  });
}

// 6. Interactive Leaflet Map
function initMap() {
  if (leafletMap) return;

  leafletMap = L.map('leafletMap').setView([40.730610, -73.935242], 11);

  // Dark Mapbox/CartoDB tiles
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap &copy; CARTO',
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(leafletMap);

  mapMarkersGroup = L.layerGroup().addTo(leafletMap);
  updateMapMarkers();
}

function updateMapMarkers() {
  if (!leafletMap || !mapMarkersGroup) return;

  mapMarkersGroup.clearLayers();
  const listingsFeed = document.getElementById('mapListingsList');
  listingsFeed.innerHTML = '';
  
  document.getElementById('mapListingsCount').textContent = filteredData.length;

  // Display top 100 markers on map for optimal performance
  const displaySubset = filteredData.slice(0, 120);

  displaySubset.forEach(item => {
    if (!item.latitude || !item.longitude) return;

    const isSuper = item.superhost_status === 'Superhost';
    const color = isSuper ? '#ff385c' : '#38bdf8';

    const marker = L.circleMarker([item.latitude, item.longitude], {
      radius: 6,
      fillColor: color,
      color: '#ffffff',
      weight: 1,
      opacity: 0.9,
      fillOpacity: 0.8
    });

    const popupContent = `
      <div style="font-family: sans-serif; padding: 4px;">
        <h4 style="margin: 0 0 4px 0; font-size: 13px; color: #1e293b;">${item.name}</h4>
        <div style="font-size: 12px; color: #64748b; margin-bottom: 6px;">
          <strong>${item.borough}</strong> &bull; ${item.room_type}
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <span style="font-weight: bold; color: #ff385c; font-size: 14px;">$${item.price} / night</span>
          <span style="background: #fef3c7; color: #b45309; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold;">
            ${item.rating} ★
          </span>
        </div>
        <a href="${item.listing_url}" target="_blank" style="display: inline-block; background: #ff385c; color: white; text-decoration: none; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: bold;">
          View on Airbnb &rarr;
        </a>
      </div>
    `;

    marker.bindPopup(popupContent);
    mapMarkersGroup.addLayer(marker);

    // Sidebar list item
    const miniCard = document.createElement('div');
    miniCard.className = 'listing-card-mini';
    miniCard.innerHTML = `
      <div class="listing-card-title">${item.name}</div>
      <div class="listing-card-meta">
        <span>${item.borough} &bull; ${item.room_type}</span>
        <span class="price-tag">$${item.price}/nt</span>
      </div>
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <span style="color: #f59e0b; font-size: 0.75rem; font-weight: 600;">${item.rating} ★ (${item.number_of_reviews} reviews)</span>
        <a href="${item.listing_url}" target="_blank" class="airbnb-link">Airbnb Link &rarr;</a>
      </div>
    `;
    listingsFeed.appendChild(miniCard);
  });
}

// 7. Populate Insights Leaderboard Table
function populateLeaderboard() {
  const tbody = document.querySelector('#tableBoroughLeaderboard tbody');
  tbody.innerHTML = '';

  const boroughs = ['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island'];
  
  boroughs.forEach(b => {
    const items = rawListingsData.filter(d => d.borough === b);
    if (!items.length) return;

    const count = items.length;
    const accom = items.reduce((a,c)=>a+c.accommodates, 0);
    const avgPrice = (items.reduce((a,c)=>a+c.price,0)/count).toFixed(2);
    const avgRating = (items.reduce((a,c)=>a+c.rating,0)/count).toFixed(2);
    const totalReviews = items.reduce((a,c)=>a+c.number_of_reviews, 0);
    const superhosts = items.filter(d => d.superhost_status === 'Superhost').length;
    const superPct = ((superhosts/count)*100).toFixed(1);

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${b}</strong></td>
      <td>${count.toLocaleString()}</td>
      <td>${accom.toLocaleString()}</td>
      <td style="color: var(--primary-pink); font-weight: bold;">$${avgPrice}</td>
      <td><span style="color: var(--accent-gold);">★ ${avgRating}</span></td>
      <td>${totalReviews.toLocaleString()}</td>
      <td><span class="pill pill-green">${superPct}%</span></td>
    `;
    tbody.appendChild(tr);
  });
}

// 8. Live SQL Query Studio Handler
function initSQLEditor() {
  const presetBtns = document.querySelectorAll('.query-preset-btn');
  const btnRun = document.getElementById('btnRunSQL');

  presetBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      presetBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const qKey = btn.getAttribute('data-query');
      document.getElementById('sqlQueryText').value = sqlPresets[qKey];
      runSQLQuery();
    });
  });

  btnRun.addEventListener('click', runSQLQuery);
}

function runSQLQuery() {
  const queryStr = document.getElementById('sqlQueryText').value;
  const startTime = performance.now();

  try {
    let res = alasql(queryStr);
    const endTime = performance.now();

    if (!Array.isArray(res)) res = [res];

    document.getElementById('sqlExecutionTime').textContent = `${(endTime - startTime).toFixed(1)} ms`;
    document.getElementById('sqlRowCount').textContent = res.length;

    renderSQLResultsTable(res);
  } catch (err) {
    console.error("SQL Execution Error:", err);
    document.getElementById('sqlRowCount').textContent = 'Error';
    document.getElementById('sqlExecutionTime').textContent = err.message;
    
    const tableHeader = document.querySelector('#sqlResultsTable thead');
    const tableBody = document.querySelector('#sqlResultsTable tbody');
    tableHeader.innerHTML = '<tr><th>Execution Error</th></tr>';
    tableBody.innerHTML = `<tr><td style="color: #ef4444; font-family: monospace;">${err.message}</td></tr>`;
  }
}

function renderSQLResultsTable(results) {
  const tableHeader = document.querySelector('#sqlResultsTable thead');
  const tableBody = document.querySelector('#sqlResultsTable tbody');

  tableHeader.innerHTML = '';
  tableBody.innerHTML = '';

  if (!results || results.length === 0) {
    tableHeader.innerHTML = '<tr><th>Result</th></tr>';
    tableBody.innerHTML = '<tr><td>No records returned.</td></tr>';
    return;
  }

  const columns = Object.keys(results[0]);
  
  // Build Header
  const trHead = document.createElement('tr');
  columns.forEach(col => {
    const th = document.createElement('th');
    th.textContent = col;
    trHead.appendChild(th);
  });
  tableHeader.appendChild(trHead);

  // Build Rows
  results.slice(0, 50).forEach(row => {
    const tr = document.createElement('tr');
    columns.forEach(col => {
      const td = document.createElement('td');
      const val = row[col];
      if (col === 'listing_url' && val) {
        td.innerHTML = `<a href="${val}" target="_blank" class="airbnb-link">Link &rarr;</a>`;
      } else {
        td.textContent = val !== null && val !== undefined ? val : 'NULL';
      }
      tr.appendChild(td);
    });
    tableBody.appendChild(tr);
  });
}

// Fallback dynamic generator if dataset json is unavailable
function generateFallbackData() {
  const boroughs = ['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island'];
  const roomTypes = ['Entire home/apt', 'Private room', 'Shared room', 'Hotel room'];
  const list = [];

  for (let i = 1; i <= 300; i++) {
    const b = boroughs[i % 5];
    const isSuper = i % 3 === 0;
    const price = 50 + (i * 3) % 400;
    list.append({
      id: 1000 + i,
      name: `Charming Studio #${i} in ${b}`,
      borough: b,
      neighbourhood: `${b} Center`,
      latitude: 40.7128 + (Math.random() - 0.5) * 0.1,
      longitude: -74.0060 + (Math.random() - 0.5) * 0.1,
      room_type: roomTypes[i % 4],
      price: price,
      accommodates: (i % 5) + 1,
      rating: +(4.2 + (i % 8) * 0.1).toFixed(2),
      number_of_reviews: (i * 7) % 250,
      superhost_status: isSuper ? 'Superhost' : 'Standard Host',
      host_is_superhost: isSuper ? 't' : 'f',
      host_tier: 'Single Listing',
      availability_365: 180,
      listing_url: `https://www.airbnb.com/rooms/${1000 + i}`
    });
  }
  return list;
}
