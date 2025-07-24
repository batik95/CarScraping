// CarScraping Dashboard JavaScript

// Global variables
let currentFilters = {};
let currentPage = 1;
let pageSize = 20;
let allSearches = [];
let filterOptions = {};
let priceChart = null;
let fuelChart = null;

// API base URL
const API_BASE = '/api';

// Initialize dashboard
async function initializeDashboard() {
    showLoading('Caricamento dashboard...');
    
    try {
        // Load initial data
        await Promise.all([
            loadFilterOptions(),
            loadSearches(),
            loadAnalytics(),
            loadCars()
        ]);
        
        // Initialize charts
        initializeCharts();
        
        // Set last update time
        updateLastUpdateTime();
        
        hideLoading();
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        showAlert('Errore nel caricamento della dashboard', 'danger');
        hideLoading();
    }
}

// Load filter options
async function loadFilterOptions() {
    try {
        const response = await fetch(`${API_BASE}/cars/filters/`);
        if (!response.ok) throw new Error('Failed to load filter options');
        
        filterOptions = await response.json();
        populateFilterDropdowns();
    } catch (error) {
        console.error('Error loading filter options:', error);
        throw error;
    }
}

// Populate filter dropdowns
function populateFilterDropdowns() {
    // Brands
    const brandSelects = ['filter-brand', 'search-brand'];
    brandSelects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            select.innerHTML = '<option value="">Tutte le marche</option>';
            filterOptions.brands.forEach(brand => {
                select.innerHTML += `<option value="${brand}">${brand}</option>`;
            });
        }
    });
    
    // Fuel types
    const fuelSelects = ['filter-fuel', 'search-fuel-type'];
    fuelSelects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            select.innerHTML = '<option value="">Tutte</option>';
            filterOptions.fuel_types.forEach(fuel => {
                select.innerHTML += `<option value="${fuel}">${fuel}</option>`;
            });
        }
    });
    
    // Transmissions
    const transmissionSelect = document.getElementById('search-transmission');
    if (transmissionSelect) {
        transmissionSelect.innerHTML = '<option value="">Tutti</option>';
        filterOptions.transmissions.forEach(trans => {
            transmissionSelect.innerHTML += `<option value="${trans}">${trans}</option>`;
        });
    }
    
    // Body types
    const bodyTypeSelect = document.getElementById('search-body-type');
    if (bodyTypeSelect) {
        bodyTypeSelect.innerHTML = '<option value="">Tutte</option>';
        filterOptions.body_types.forEach(body => {
            bodyTypeSelect.innerHTML += `<option value="${body}">${body}</option>`;
        });
    }
    
    // Colors
    const colorSelect = document.getElementById('search-color');
    if (colorSelect) {
        colorSelect.innerHTML = '<option value="">Tutti i colori</option>';
        filterOptions.colors.forEach(color => {
            colorSelect.innerHTML += `<option value="${color}">${color}</option>`;
        });
    }
    
    // Provinces
    const provinceSelect = document.getElementById('search-province');
    if (provinceSelect) {
        provinceSelect.innerHTML = '<option value="">Tutte le province</option>';
        filterOptions.provinces.forEach(province => {
            provinceSelect.innerHTML += `<option value="${province}">${province}</option>`;
        });
    }
}

// Update models based on selected brand
async function updateModels() {
    const brandSelect = document.getElementById('filter-brand') || document.getElementById('search-brand');
    const modelSelect = document.getElementById('filter-model') || document.getElementById('search-model');
    
    if (!brandSelect || !modelSelect) return;
    
    const selectedBrand = brandSelect.value;
    modelSelect.innerHTML = '<option value="">Tutti i modelli</option>';
    
    if (selectedBrand) {
        try {
            const response = await fetch(`${API_BASE}/cars/models/${selectedBrand}`);
            if (response.ok) {
                const data = await response.json();
                data.models.forEach(model => {
                    modelSelect.innerHTML += `<option value="${model}">${model}</option>`;
                });
            }
        } catch (error) {
            console.error('Error loading models:', error);
        }
    }
}

// Load searches
async function loadSearches() {
    try {
        const response = await fetch(`${API_BASE}/searches/`);
        if (!response.ok) throw new Error('Failed to load searches');
        
        allSearches = await response.json();
        populateSearchesTable();
        populateSearchFilter();
    } catch (error) {
        console.error('Error loading searches:', error);
        throw error;
    }
}

// Populate searches table
function populateSearchesTable() {
    const tbody = document.getElementById('searches-table');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    allSearches.forEach(search => {
        const row = document.createElement('tr');
        
        const priceRange = formatPriceRange(search.price_min, search.price_max);
        const yearRange = formatYearRange(search.year_min, search.year_max);
        const status = search.is_active ? 
            '<span class="badge bg-success">Attiva</span>' : 
            '<span class="badge bg-secondary">Inattiva</span>';
        
        row.innerHTML = `
            <td>${search.name}</td>
            <td>${search.brand || '-'}</td>
            <td>${search.model || '-'}</td>
            <td>${priceRange}</td>
            <td>${yearRange}</td>
            <td>${status}</td>
            <td>${formatDate(search.updated_at || search.created_at)}</td>
            <td class="action-buttons">
                <button class="btn btn-sm btn-outline-primary" onclick="editSearch(${search.id})" title="Modifica">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-outline-success" onclick="runSearchScraping(${search.id})" title="Esegui Scraping">
                    <i class="fas fa-play"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteSearch(${search.id})" title="Elimina">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// Populate search filter dropdown
function populateSearchFilter() {
    const select = document.getElementById('filter-search');
    if (!select) return;
    
    select.innerHTML = '<option value="">Tutte le ricerche</option>';
    allSearches.forEach(search => {
        select.innerHTML += `<option value="${search.id}">${search.name}</option>`;
    });
}

// Load analytics
async function loadAnalytics() {
    try {
        const params = new URLSearchParams(currentFilters);
        const response = await fetch(`${API_BASE}/analytics/?${params}`);
        if (!response.ok) throw new Error('Failed to load analytics');
        
        const analytics = await response.json();
        updateKPIs(analytics);
        updateMileageStats(analytics.mileage_stats);
        updateCharts(analytics);
    } catch (error) {
        console.error('Error loading analytics:', error);
        throw error;
    }
}

// Update KPIs
function updateKPIs(analytics) {
    document.getElementById('kpi-total-cars').textContent = analytics.total_cars;
    document.getElementById('kpi-avg-price').textContent = formatPrice(analytics.price_stats.avg_price);
    document.getElementById('kpi-price-range').textContent = 
        `${formatPrice(analytics.price_stats.min_price)} - ${formatPrice(analytics.price_stats.max_price)}`;
    document.getElementById('kpi-avg-age').textContent = `${Math.round(analytics.avg_age_years)} anni`;
}

// Update mileage statistics
function updateMileageStats(mileageStats) {
    // 0-50k range
    document.getElementById('mileage-0-50k-price').textContent = formatPrice(mileageStats.range_0_50k.avg_price);
    document.getElementById('mileage-0-50k-count').textContent = `${mileageStats.range_0_50k.count} auto`;
    
    // 50-100k range
    document.getElementById('mileage-50-100k-price').textContent = formatPrice(mileageStats.range_50_100k.avg_price);
    document.getElementById('mileage-50-100k-count').textContent = `${mileageStats.range_50_100k.count} auto`;
    
    // 100k+ range
    document.getElementById('mileage-100k-plus-price').textContent = formatPrice(mileageStats.range_100k_plus.avg_price);
    document.getElementById('mileage-100k-plus-count').textContent = `${mileageStats.range_100k_plus.count} auto`;
}

// Load cars
async function loadCars() {
    try {
        const params = new URLSearchParams({
            ...currentFilters,
            skip: (currentPage - 1) * pageSize,
            limit: pageSize
        });
        
        const response = await fetch(`${API_BASE}/cars/?${params}`);
        if (!response.ok) throw new Error('Failed to load cars');
        
        const cars = await response.json();
        populateCarsTable(cars);
    } catch (error) {
        console.error('Error loading cars:', error);
        throw error;
    }
}

// Populate cars table
function populateCarsTable(cars) {
    const tbody = document.getElementById('cars-table');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    cars.forEach(car => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${car.brand}</td>
            <td>${car.model}</td>
            <td class="year-cell">${car.year || '-'}</td>
            <td class="mileage-cell">${formatMileage(car.mileage)}</td>
            <td class="price-cell">${formatPrice(car.price)}</td>
            <td>${car.fuel_type || '-'}</td>
            <td>${car.province || '-'}</td>
            <td>${formatDate(car.last_seen)}</td>
            <td class="action-buttons">
                <a href="${car.url}" target="_blank" class="btn btn-sm btn-outline-primary" title="Visualizza Annuncio">
                    <i class="fas fa-external-link-alt"></i>
                </a>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Initialize charts
function initializeCharts() {
    // Price trend chart
    const priceCtx = document.getElementById('priceChart');
    if (priceCtx) {
        priceChart = new Chart(priceCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Prezzo Medio',
                    data: [],
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return '€' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Fuel distribution chart
    const fuelCtx = document.getElementById('fuelChart');
    if (fuelCtx) {
        fuelChart = new Chart(fuelCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#0d6efd', '#198754', '#ffc107', '#dc3545', '#6c757d', '#20c997'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }
}

// Update charts with analytics data
function updateCharts(analytics) {
    // Update price trend chart
    if (priceChart && analytics.price_trends) {
        priceChart.data.labels = analytics.price_trends.map(trend => 
            new Date(trend.date).toLocaleDateString('it-IT')
        );
        priceChart.data.datasets[0].data = analytics.price_trends.map(trend => trend.avg_price);
        priceChart.update();
    }
    
    // Update fuel distribution chart
    if (fuelChart && analytics.fuel_type_distribution) {
        const fuelData = Object.entries(analytics.fuel_type_distribution);
        fuelChart.data.labels = fuelData.map(([fuel, count]) => fuel);
        fuelChart.data.datasets[0].data = fuelData.map(([fuel, count]) => count);
        fuelChart.update();
    }
}

// Apply filters
async function applyFilters() {
    // Collect filter values
    currentFilters = {};
    
    const searchId = document.getElementById('filter-search')?.value;
    const brand = document.getElementById('filter-brand')?.value;
    const model = document.getElementById('filter-model')?.value;
    const fuel = document.getElementById('filter-fuel')?.value;
    const priceMin = document.getElementById('filter-price-min')?.value;
    const priceMax = document.getElementById('filter-price-max')?.value;
    const yearMin = document.getElementById('filter-year-min')?.value;
    const yearMax = document.getElementById('filter-year-max')?.value;
    
    if (searchId) currentFilters.search_id = searchId;
    if (brand) currentFilters.brand = brand;
    if (model) currentFilters.model = model;
    if (fuel) currentFilters.fuel_type = fuel;
    if (priceMin) currentFilters.min_price = priceMin;
    if (priceMax) currentFilters.max_price = priceMax;
    if (yearMin) currentFilters.min_year = yearMin;
    if (yearMax) currentFilters.max_year = yearMax;
    
    // Reset page
    currentPage = 1;
    
    // Reload data
    try {
        await Promise.all([
            loadAnalytics(),
            loadCars()
        ]);
    } catch (error) {
        showAlert('Errore nell\'applicazione dei filtri', 'danger');
    }
}

// Apply search filter
async function applySearchFilter() {
    const searchId = document.getElementById('filter-search').value;
    
    if (searchId) {
        // Find the search and populate other filters
        const search = allSearches.find(s => s.id == searchId);
        if (search) {
            if (search.brand) document.getElementById('filter-brand').value = search.brand;
            if (search.model) document.getElementById('filter-model').value = search.model;
            if (search.fuel_type) document.getElementById('filter-fuel').value = search.fuel_type;
            if (search.price_min) document.getElementById('filter-price-min').value = search.price_min;
            if (search.price_max) document.getElementById('filter-price-max').value = search.price_max;
            if (search.year_min) document.getElementById('filter-year-min').value = search.year_min;
            if (search.year_max) document.getElementById('filter-year-max').value = search.year_max;
        }
    }
    
    await applyFilters();
}

// Clear filters
async function clearFilters() {
    document.getElementById('filter-search').value = '';
    document.getElementById('filter-brand').value = '';
    document.getElementById('filter-model').value = '';
    document.getElementById('filter-fuel').value = '';
    document.getElementById('filter-price-min').value = '';
    document.getElementById('filter-price-max').value = '';
    document.getElementById('filter-year-min').value = '';
    document.getElementById('filter-year-max').value = '';
    
    await applyFilters();
}

// Save search
async function saveSearch() {
    const form = document.getElementById('searchForm');
    const formData = new FormData(form);
    const searchData = {};
    
    // Convert FormData to object
    for (let [key, value] of formData.entries()) {
        if (value) {
            // Convert numeric fields
            if (['year_min', 'year_max', 'mileage_min', 'mileage_max', 'power_min', 'power_max'].includes(key)) {
                searchData[key] = parseInt(value);
            } else if (['price_min', 'price_max'].includes(key)) {
                searchData[key] = parseFloat(value);
            } else {
                searchData[key] = value;
            }
        }
    }
    
    try {
        const searchId = document.getElementById('search-id').value;
        const method = searchId ? 'PUT' : 'POST';
        const url = searchId ? `${API_BASE}/searches/${searchId}` : `${API_BASE}/searches/`;
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(searchData)
        });
        
        if (!response.ok) throw new Error('Failed to save search');
        
        // Close modal and refresh data
        bootstrap.Modal.getInstance(document.getElementById('searchModal')).hide();
        await loadSearches();
        showAlert('Ricerca salvata con successo', 'success');
        
    } catch (error) {
        console.error('Error saving search:', error);
        showAlert('Errore nel salvataggio della ricerca', 'danger');
    }
}

// Edit search
function editSearch(searchId) {
    const search = allSearches.find(s => s.id === searchId);
    if (!search) return;
    
    // Populate form
    document.getElementById('search-id').value = search.id;
    document.getElementById('search-name').value = search.name;
    document.getElementById('search-brand').value = search.brand || '';
    document.getElementById('search-model').value = search.model || '';
    document.getElementById('search-fuel-type').value = search.fuel_type || '';
    document.getElementById('search-transmission').value = search.transmission || '';
    document.getElementById('search-body-type').value = search.body_type || '';
    document.getElementById('search-color').value = search.color || '';
    document.getElementById('search-province').value = search.province || '';
    document.getElementById('search-price-min').value = search.price_min || '';
    document.getElementById('search-price-max').value = search.price_max || '';
    document.getElementById('search-year-min').value = search.year_min || '';
    document.getElementById('search-year-max').value = search.year_max || '';
    document.getElementById('search-mileage-min').value = search.mileage_min || '';
    document.getElementById('search-mileage-max').value = search.mileage_max || '';
    document.getElementById('search-power-min').value = search.power_min || '';
    document.getElementById('search-power-max').value = search.power_max || '';
    
    // Update modal title
    document.getElementById('modal-title').textContent = 'Modifica Ricerca';
    
    // Show modal
    new bootstrap.Modal(document.getElementById('searchModal')).show();
}

// Reset search form
function resetSearchForm() {
    document.getElementById('searchForm').reset();
    document.getElementById('search-id').value = '';
    document.getElementById('modal-title').textContent = 'Nuova Ricerca';
}

// Delete search
async function deleteSearch(searchId) {
    if (!confirm('Sei sicuro di voler eliminare questa ricerca?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/searches/${searchId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete search');
        
        await loadSearches();
        showAlert('Ricerca eliminata con successo', 'success');
        
    } catch (error) {
        console.error('Error deleting search:', error);
        showAlert('Errore nell\'eliminazione della ricerca', 'danger');
    }
}

// Run search scraping
async function runSearchScraping(searchId) {
    if (!confirm('Avviare lo scraping per questa ricerca?')) return;
    
    showLoading('Esecuzione scraping in corso...');
    
    try {
        const response = await fetch(`${API_BASE}/searches/${searchId}/run`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Failed to run scraping');
        
        const result = await response.json();
        hideLoading();
        
        showAlert(`Scraping completato: ${result.cars_found} auto trovate, ${result.cars_new} nuove`, 'success');
        
        // Refresh data
        await Promise.all([
            loadAnalytics(),
            loadCars()
        ]);
        
    } catch (error) {
        console.error('Error running scraping:', error);
        hideLoading();
        showAlert('Errore nell\'esecuzione dello scraping', 'danger');
    }
}

// Run general search
async function runSearch() {
    await applyFilters();
    showAlert('Dati aggiornati', 'info');
}

// Refresh all data
async function refreshData() {
    showLoading('Aggiornamento dati...');
    
    try {
        await Promise.all([
            loadFilterOptions(),
            loadSearches(),
            loadAnalytics(),
            loadCars()
        ]);
        
        updateLastUpdateTime();
        hideLoading();
        showAlert('Dati aggiornati con successo', 'success');
        
    } catch (error) {
        console.error('Error refreshing data:', error);
        hideLoading();
        showAlert('Errore nell\'aggiornamento dei dati', 'danger');
    }
}

// Export data
function exportData() {
    // Create CSV content
    const csvContent = generateCSV();
    
    // Create download link
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `carscraping_export_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Generate CSV content
function generateCSV() {
    // This is a simplified version - in a real app you'd fetch all data
    const headers = ['Marca', 'Modello', 'Anno', 'Chilometraggio', 'Prezzo', 'Alimentazione', 'Provincia'];
    const rows = [headers.join(',')];
    
    // Add current table data
    const tableRows = document.querySelectorAll('#cars-table tr');
    tableRows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length >= 7) {
            const rowData = Array.from(cells).slice(0, 7).map(cell => 
                `"${cell.textContent.trim()}"`
            );
            rows.push(rowData.join(','));
        }
    });
    
    return rows.join('\n');
}

// Utility functions
function formatPrice(price) {
    if (!price) return '€0';
    return '€' + Math.round(price).toLocaleString('it-IT');
}

function formatMileage(mileage) {
    if (!mileage) return '-';
    return Math.round(mileage).toLocaleString('it-IT') + ' km';
}

function formatDate(dateString) {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('it-IT');
}

function formatPriceRange(min, max) {
    if (!min && !max) return '-';
    if (!min) return `≤ ${formatPrice(max)}`;
    if (!max) return `≥ ${formatPrice(min)}`;
    return `${formatPrice(min)} - ${formatPrice(max)}`;
}

function formatYearRange(min, max) {
    if (!min && !max) return '-';
    if (!min) return `≤ ${max}`;
    if (!max) return `≥ ${min}`;
    return `${min} - ${max}`;
}

function showLoading(message = 'Caricamento...') {
    document.getElementById('loading-message').textContent = message;
    new bootstrap.Modal(document.getElementById('loadingModal')).show();
}

function hideLoading() {
    const modal = bootstrap.Modal.getInstance(document.getElementById('loadingModal'));
    if (modal) modal.hide();
}

function showAlert(message, type = 'info') {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

function updateLastUpdateTime() {
    document.getElementById('last-update').textContent = new Date().toLocaleTimeString('it-IT');
}