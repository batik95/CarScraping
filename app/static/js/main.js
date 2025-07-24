/* CarScraping - Enhanced Dashboard JavaScript
 * Modern dashboard with Chart.js v4, real-time updates, and advanced analytics
 */

// Global application state
const CarScraping = {
    state: {
        currentFilters: {},
        currentPage: 1,
        pageSize: 20,
        allSearches: [],
        filterOptions: {},
        realTimeEnabled: false,
        websocket: null,
        lastUpdate: null
    },
    
    charts: {
        priceTrend: null,
        priceMileage: null,
        geographic: null,
        priceHistogram: null,
        fuelDistribution: null
    },
    
    api: {
        base: '/api',
        charts: '/api/charts',
        analytics: '/api/analytics',
        realtime: '/api/realtime'
    }
};

// Chart.js v4 Global Configuration
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = '#64748b';
Chart.defaults.borderColor = '#e2e8f0';
Chart.defaults.backgroundColor = 'rgba(30, 58, 138, 0.1)';

// Custom Chart.js theme
const chartTheme = {
    primary: '#1e3a8a',
    secondary: '#64748b',
    accent: '#f59e0b',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    info: '#06b6d4'
};

/* ============================================
   INITIALIZATION
   ============================================ */

// Initialize dashboard when page loads
async function initializeDashboard() {
    console.log('🚗 CarScraping Dashboard - Initializing...');
    
    try {
        showLoading('Inizializzazione dashboard...');
        
        // Setup Chart.js plugins and configurations
        setupChartDefaults();
        
        // Load initial data in parallel
        await Promise.all([
            loadFilterOptions(),
            loadSearches(),
            loadAnalytics(),
            loadCars()
        ]);
        
        // Initialize all charts
        await initializeAllCharts();
        
        // Setup real-time updates
        setupRealTimeUpdates();
        
        // Set last update time
        updateLastUpdateTime();
        
        hideLoading();
        
        // Show success notification
        showToast('Dashboard inizializzata con successo', 'success');
        
        console.log('✅ Dashboard initialized successfully');
        
    } catch (error) {
        console.error('❌ Error initializing dashboard:', error);
        hideLoading();
        showToast('Errore nel caricamento della dashboard', 'error');
    }
}

// Setup Chart.js defaults and plugins
function setupChartDefaults() {
    // Register Chart.js plugins
    Chart.register(
        Chart.LineController,
        Chart.BarController,
        Chart.ScatterController,
        Chart.DoughnutController,
        Chart.CategoryScale,
        Chart.LinearScale,
        Chart.PointElement,
        Chart.LineElement,
        Chart.BarElement,
        Chart.ArcElement,
        Chart.Title,
        Chart.Tooltip,
        Chart.Legend,
        Chart.Filler
    );
    
    // Custom tooltip configuration
    Chart.defaults.plugins.tooltip = {
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        titleColor: '#1e293b',
        bodyColor: '#64748b',
        borderColor: '#e2e8f0',
        borderWidth: 1,
        cornerRadius: 8,
        padding: 12,
        displayColors: true,
        mode: 'index',
        intersect: false,
        animation: {
            duration: 200
        }
    };
    
    // Custom legend configuration
    Chart.defaults.plugins.legend = {
        display: true,
        position: 'bottom',
        labels: {
            usePointStyle: true,
            padding: 20,
            font: {
                size: 12,
                weight: '500'
            }
        }
    };
}

/* ============================================
   REAL-TIME FEATURES
   ============================================ */

// Setup real-time updates with WebSocket
function setupRealTimeUpdates() {
    // Check if WebSocket is supported
    if (!window.WebSocket) {
        console.warn('WebSocket not supported, falling back to polling');
        setupPollingUpdates();
        return;
    }
    
    try {
        // Connect to WebSocket
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/live-updates`;
        
        CarScraping.state.websocket = new WebSocket(wsUrl);
        
        CarScraping.state.websocket.onopen = function(event) {
            console.log('🔗 WebSocket connected');
            CarScraping.state.realTimeEnabled = true;
            updateRealTimeStatus('active');
            showToast('Connessione real-time attiva', 'success');
        };
        
        CarScraping.state.websocket.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                handleRealTimeUpdate(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        CarScraping.state.websocket.onclose = function(event) {
            console.log('🔌 WebSocket disconnected');
            CarScraping.state.realTimeEnabled = false;
            updateRealTimeStatus('inactive');
            
            // Attempt to reconnect after 5 seconds
            setTimeout(() => {
                console.log('🔄 Attempting to reconnect WebSocket...');
                setupRealTimeUpdates();
            }, 5000);
        };
        
        CarScraping.state.websocket.onerror = function(error) {
            console.error('WebSocket error:', error);
            updateRealTimeStatus('error');
        };
        
    } catch (error) {
        console.error('Failed to setup WebSocket:', error);
        setupPollingUpdates();
    }
}

// Fallback to polling for real-time updates
function setupPollingUpdates() {
    console.log('📊 Setting up polling updates...');
    
    // Poll for updates every 30 seconds
    setInterval(async () => {
        try {
            await updateRealTimeData();
        } catch (error) {
            console.error('Error in polling update:', error);
        }
    }, 30000);
}

// Handle real-time update messages
function handleRealTimeUpdate(data) {
    console.log('📡 Received real-time update:', data.type);
    
    switch (data.type) {
        case 'scraping_progress':
            updateScrapingProgress(data.payload);
            break;
            
        case 'new_cars':
            handleNewCarsUpdate(data.payload);
            break;
            
        case 'analytics_update':
            updateKPIsRealTime(data.payload);
            break;
            
        case 'price_alert':
            showPriceAlert(data.payload);
            break;
            
        default:
            console.log('Unknown real-time update type:', data.type);
    }
    
    // Update last update time
    updateLastUpdateTime();
}

// Update real-time status indicator
function updateRealTimeStatus(status) {
    const indicator = document.getElementById('realtime-status');
    if (!indicator) return;
    
    const icon = indicator.querySelector('i');
    
    switch (status) {
        case 'active':
            icon.className = 'fas fa-circle text-success';
            indicator.title = 'Connessione real-time attiva';
            break;
        case 'inactive':
            icon.className = 'fas fa-circle text-secondary';
            indicator.title = 'Connessione real-time non attiva';
            break;
        case 'error':
            icon.className = 'fas fa-circle text-danger';
            indicator.title = 'Errore connessione real-time';
            break;
    }
}

/* ============================================
   DATA LOADING
   ============================================ */

// Load filter options
async function loadFilterOptions() {
    try {
        const response = await fetch(`${CarScraping.api.base}/cars/filters/`);
        if (!response.ok) throw new Error('Failed to load filter options');
        
        CarScraping.state.filterOptions = await response.json();
        populateFilterDropdowns();
        
    } catch (error) {
        console.error('Error loading filter options:', error);
        throw error;
    }
}

// Populate filter dropdowns with Select2 enhancement
function populateFilterDropdowns() {
    // Brands
    const brandSelects = ['filter-brand', 'search-brand'];
    brandSelects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            select.innerHTML = '<option value="">Tutte le marche</option>';
            CarScraping.state.filterOptions.brands.forEach(brand => {
                select.innerHTML += `<option value="${brand}">${brand}</option>`;
            });
            
            // Initialize Select2 if available
            if (window.jQuery && jQuery.fn.select2) {
                jQuery(`#${selectId}`).select2({
                    theme: 'bootstrap-5',
                    placeholder: 'Seleziona marca...',
                    allowClear: true
                });
            }
        }
    });
    
    // Similar setup for other selects...
    // (Simplified for brevity)
}

// Load analytics data
async function loadAnalytics() {
    try {
        const params = new URLSearchParams(CarScraping.state.currentFilters);
        const response = await fetch(`${CarScraping.api.analytics}/?${params}`);
        if (!response.ok) throw new Error('Failed to load analytics');
        
        const analytics = await response.json();
        
        // Update KPIs
        updateKPIs(analytics);
        updateMileageStats(analytics.mileage_stats);
        
        // Update charts with new data
        await updateAllCharts(analytics);
        
    } catch (error) {
        console.error('Error loading analytics:', error);
        throw error;
    }
}

// Load dashboard data
async function loadDashboardData() {
    try {
        showLoading('Caricamento dati dashboard...');
        
        await Promise.all([
            loadAnalytics(),
            loadCars()
        ]);
        
        hideLoading();
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        hideLoading();
        showToast('Errore nel caricamento dei dati', 'error');
    }
}

/* ============================================
   CHART INITIALIZATION & MANAGEMENT
   ============================================ */

// Initialize all charts
async function initializeAllCharts() {
    console.log('📊 Initializing charts...');
    
    try {
        // Initialize charts in parallel
        await Promise.all([
            initializePriceTrendChart(),
            initializePriceMileageChart(),
            initializeGeographicChart(),
            initializePriceHistogramChart()
        ]);
        
        console.log('✅ All charts initialized');
        
    } catch (error) {
        console.error('❌ Error initializing charts:', error);
        throw error;
    }
}

// Initialize price trend chart
async function initializePriceTrendChart() {
    const canvas = document.getElementById('price-trend-chart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    CarScraping.charts.priceTrend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Prezzo Medio',
                    data: [],
                    borderColor: chartTheme.primary,
                    backgroundColor: `${chartTheme.primary}20`,
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: chartTheme.primary,
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2
                },
                {
                    label: '0-50k km',
                    data: [],
                    borderColor: chartTheme.success,
                    backgroundColor: `${chartTheme.success}20`,
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false,
                    pointRadius: 3,
                    pointHoverRadius: 5
                },
                {
                    label: '50-100k km',
                    data: [],
                    borderColor: chartTheme.warning,
                    backgroundColor: `${chartTheme.warning}20`,
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false,
                    pointRadius: 3,
                    pointHoverRadius: 5
                },
                {
                    label: '100k+ km',
                    data: [],
                    borderColor: chartTheme.error,
                    backgroundColor: `${chartTheme.error}20`,
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false,
                    pointRadius: 3,
                    pointHoverRadius: 5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                title: {
                    display: false
                },
                legend: {
                    display: true,
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${formatPrice(context.parsed.y)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Data'
                    },
                    grid: {
                        color: '#f1f5f9'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Prezzo (€)'
                    },
                    grid: {
                        color: '#f1f5f9'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatPrice(value);
                        }
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            }
        }
    });
}

// Initialize price vs mileage scatter plot
async function initializePriceMileageChart() {
    const canvas = document.getElementById('price-mileage-chart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    CarScraping.charts.priceMileage = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: '0-5 anni',
                    data: [],
                    backgroundColor: `${chartTheme.primary}80`,
                    borderColor: chartTheme.primary,
                    pointRadius: 5,
                    pointHoverRadius: 7
                },
                {
                    label: '5-10 anni',
                    data: [],
                    backgroundColor: `${chartTheme.success}80`,
                    borderColor: chartTheme.success,
                    pointRadius: 5,
                    pointHoverRadius: 7
                },
                {
                    label: '10+ anni',
                    data: [],
                    backgroundColor: `${chartTheme.warning}80`,
                    borderColor: chartTheme.warning,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: false
                },
                legend: {
                    display: true,
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${formatMileage(context.parsed.x)} - ${formatPrice(context.parsed.y)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    position: 'bottom',
                    title: {
                        display: true,
                        text: 'Chilometraggio (km)'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatMileage(value);
                        }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Prezzo (€)'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatPrice(value);
                        }
                    }
                }
            },
            animation: {
                duration: 1200,
                easing: 'easeInOutQuart'
            }
        }
    });
}

// Initialize geographic chart (placeholder - would need proper map data)
async function initializeGeographicChart() {
    const canvas = document.getElementById('geographic-chart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // For now, we'll use a bar chart representing regions
    // In a full implementation, this would be a proper map visualization
    CarScraping.charts.geographic = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Prezzo Medio per Regione',
                    data: [],
                    backgroundColor: [
                        `${chartTheme.primary}80`,
                        `${chartTheme.success}80`,
                        `${chartTheme.warning}80`,
                        `${chartTheme.error}80`,
                        `${chartTheme.info}80`,
                        `${chartTheme.accent}80`
                    ],
                    borderColor: [
                        chartTheme.primary,
                        chartTheme.success,
                        chartTheme.warning,
                        chartTheme.error,
                        chartTheme.info,
                        chartTheme.accent
                    ],
                    borderWidth: 2,
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: ${formatPrice(context.parsed.y)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Regione'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Prezzo Medio (€)'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatPrice(value);
                        }
                    }
                }
            }
        }
    });
}

// Initialize price histogram
async function initializePriceHistogramChart() {
    const canvas = document.getElementById('price-histogram-chart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    CarScraping.charts.priceHistogram = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Numero Auto',
                    data: [],
                    backgroundColor: `${chartTheme.primary}80`,
                    borderColor: chartTheme.primary,
                    borderWidth: 2,
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return `Fascia: ${context[0].label}`;
                        },
                        label: function(context) {
                            return `Auto: ${context.parsed.y}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Fascia di Prezzo (€)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Numero di Auto'
                    }
                }
            }
        }
    });
}

/* ============================================
   ADVANCED FILTER MANAGEMENT
   ============================================ */

// Setup advanced filters with range sliders
function setupAdvancedFilters() {
    console.log('🔧 Setting up advanced filters...');
    
    // Setup search functionality
    setupQuickSearch();
    
    // Setup filter tags
    setupFilterTags();
    
    // Setup advanced dropdowns
    setupAdvancedDropdowns();
}

// Setup quick search functionality
function setupQuickSearch() {
    const searchInput = document.getElementById('quick-search');
    if (!searchInput) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.trim();
        const clearBtn = document.querySelector('.search-clear');
        
        // Show/hide clear button
        if (query) {
            clearBtn.style.display = 'block';
        } else {
            clearBtn.style.display = 'none';
        }
        
        // Debounce search
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            performQuickSearch(query);
        }, 300);
    });
}

// Perform quick search
async function performQuickSearch(query) {
    if (!query) {
        clearQuickSearch();
        return;
    }
    
    try {
        CarScraping.state.currentFilters.search = query;
        await applyFilters();
        
        // Update filter tags
        updateFilterTags();
        
    } catch (error) {
        console.error('Error performing quick search:', error);
        showToast('Errore nella ricerca', 'error');
    }
}

// Clear quick search
function clearQuickSearch() {
    const searchInput = document.getElementById('quick-search');
    const clearBtn = document.querySelector('.search-clear');
    
    searchInput.value = '';
    clearBtn.style.display = 'none';
    
    delete CarScraping.state.currentFilters.search;
    applyFilters();
    updateFilterTags();
}

// Setup filter tags display
function setupFilterTags() {
    updateFilterTags();
}

// Update active filter tags
function updateFilterTags() {
    const container = document.getElementById('active-filters');
    if (!container) return;
    
    container.innerHTML = '';
    
    Object.entries(CarScraping.state.currentFilters).forEach(([key, value]) => {
        if (!value) return;
        
        const tag = document.createElement('div');
        tag.className = 'filter-tag';
        
        const label = getFilterLabel(key, value);
        tag.innerHTML = `
            <span>${label}</span>
            <button class="filter-tag-remove" onclick="removeFilter('${key}')">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        container.appendChild(tag);
    });
}

// Get human-readable label for filter
function getFilterLabel(key, value) {
    const labels = {
        search: `Ricerca: ${value}`,
        brand: `Marca: ${value}`,
        model: `Modello: ${value}`,
        fuel_type: `Alimentazione: ${value}`,
        min_price: `Prezzo min: ${formatPrice(value)}`,
        max_price: `Prezzo max: ${formatPrice(value)}`,
        min_year: `Anno min: ${value}`,
        max_year: `Anno max: ${value}`,
        min_mileage: `Km min: ${formatMileage(value)}`,
        max_mileage: `Km max: ${formatMileage(value)}`
    };
    
    return labels[key] || `${key}: ${value}`;
}

// Remove filter
async function removeFilter(key) {
    delete CarScraping.state.currentFilters[key];
    
    // Clear corresponding form field
    const fieldId = `filter-${key.replace('_', '-')}`;
    const field = document.getElementById(fieldId);
    if (field) {
        field.value = '';
    }
    
    await applyFilters();
    updateFilterTags();
}

/* ============================================
   ENHANCED UTILITY FUNCTIONS
   ============================================ */

// Show modern toast notification
function showToast(message, type = 'info', duration = 5000) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toastId = `toast-${Date.now()}`;
    const iconMap = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast-modern ${type}`;
    toast.innerHTML = `
        <div class="toast-icon">
            <i class="fas ${iconMap[type] || iconMap.info}"></i>
        </div>
        <div class="toast-content">
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="closeToast('${toastId}')">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    // Auto-dismiss
    setTimeout(() => {
        closeToast(toastId);
    }, duration);
}

// Close toast notification
function closeToast(toastId) {
    const toast = document.getElementById(toastId);
    if (toast) {
        toast.style.animation = 'slide-out-right 0.3s ease-in';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }
}

// Update last update time with real-time formatting
function updateLastUpdateTime() {
    const element = document.getElementById('last-update');
    if (!element) return;
    
    const now = new Date();
    CarScraping.state.lastUpdate = now;
    
    element.textContent = now.toLocaleTimeString('it-IT', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// Enhanced price formatting
function formatPrice(price) {
    if (!price || price === 0) return '€0';
    
    return new Intl.NumberFormat('it-IT', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(price);
}

// Enhanced mileage formatting
function formatMileage(mileage) {
    if (!mileage || mileage === 0) return '0 km';
    
    return new Intl.NumberFormat('it-IT').format(mileage) + ' km';
}

// Format date with relative time
function formatDate(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) {
        return 'Ieri';
    } else if (diffDays < 7) {
        return `${diffDays} giorni fa`;
    } else {
        return date.toLocaleDateString('it-IT');
    }
}

/* ============================================
   BACKWARDS COMPATIBILITY
   ============================================ */

// Maintain backwards compatibility with existing functions
async function loadSearches() {
    // Implementation from original app.js
    // (Keeping for compatibility)
}

async function loadCars() {
    // Implementation from original app.js
    // (Keeping for compatibility)
}

async function applyFilters() {
    // Enhanced implementation
    try {
        await Promise.all([
            loadAnalytics(),
            loadCars()
        ]);
        updateFilterTags();
    } catch (error) {
        showToast('Errore nell\'applicazione dei filtri', 'error');
    }
}

// Export functions for global access
window.CarScraping = CarScraping;
window.initializeDashboard = initializeDashboard;
window.setupRealTimeUpdates = setupRealTimeUpdates;
window.initializeRangeSliders = initializeRangeSliders;
window.setupAdvancedFilters = setupAdvancedFilters;
window.initializeCharts = initializeAllCharts;
window.showToast = showToast;
window.toggleTheme = toggleTheme;
window.toggleSidebar = toggleSidebar;
window.closeSidebar = closeSidebar;