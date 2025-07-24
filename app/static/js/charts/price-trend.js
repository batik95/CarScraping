/* CarScraping - Price Trend Chart Module
 * Advanced price trend analysis with Chart.js v4
 */

// Price Trend Chart Controller
class PriceTrendChart {
    constructor(canvasId) {
        this.canvasId = canvasId;
        this.chart = null;
        this.currentPeriod = '30d';
        this.isLoading = false;
    }

    // Initialize the chart
    async initialize() {
        const canvas = document.getElementById(this.canvasId);
        if (!canvas) {
            throw new Error(`Canvas element with id '${this.canvasId}' not found`);
        }

        const ctx = canvas.getContext('2d');
        
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: this.getChartOptions(),
            plugins: [this.getZoomPlugin(), this.getAnnotationPlugin()]
        });

        // Setup period controls
        this.setupPeriodControls();
        
        // Load initial data
        await this.loadData(this.currentPeriod);
    }

    // Get chart configuration options
    getChartOptions() {
        return {
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
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        font: {
                            size: 12,
                            weight: '500'
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    titleColor: '#1e293b',
                    bodyColor: '#64748b',
                    borderColor: '#e2e8f0',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        title: (context) => {
                            const date = new Date(context[0].label);
                            return date.toLocaleDateString('it-IT', {
                                weekday: 'long',
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric'
                            });
                        },
                        label: (context) => {
                            const label = context.dataset.label || '';
                            const value = this.formatPrice(context.parsed.y);
                            const change = this.calculateChange(context);
                            return `${label}: ${value}${change}`;
                        },
                        afterBody: (context) => {
                            // Show additional statistics
                            if (context.length > 0) {
                                const data = context[0].dataset.data;
                                const currentIndex = context[0].dataIndex;
                                const trend = this.calculateTrend(data, currentIndex);
                                return [`Trend: ${trend}`];
                            }
                            return [];
                        }
                    }
                },
                zoom: {
                    pan: {
                        enabled: true,
                        mode: 'x'
                    },
                    zoom: {
                        wheel: {
                            enabled: true
                        },
                        pinch: {
                            enabled: true
                        },
                        mode: 'x'
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        parser: 'YYYY-MM-DD',
                        tooltipFormat: 'DD/MM/YYYY',
                        displayFormats: {
                            day: 'DD/MM',
                            week: 'DD/MM',
                            month: 'MMM YYYY'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Data',
                        font: {
                            size: 12,
                            weight: '600'
                        }
                    },
                    grid: {
                        color: '#f1f5f9',
                        borderColor: '#e2e8f0'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Prezzo (€)',
                        font: {
                            size: 12,
                            weight: '600'
                        }
                    },
                    grid: {
                        color: '#f1f5f9',
                        borderColor: '#e2e8f0'
                    },
                    ticks: {
                        callback: (value) => this.formatPrice(value)
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            },
            elements: {
                point: {
                    radius: 3,
                    hoverRadius: 6,
                    borderWidth: 2,
                    hoverBorderWidth: 3
                },
                line: {
                    tension: 0.4,
                    borderWidth: 3,
                    borderCapStyle: 'round',
                    borderJoinStyle: 'round'
                }
            }
        };
    }

    // Setup period control buttons
    setupPeriodControls() {
        const controls = document.querySelectorAll(`[data-chart="price-trend"] .chart-control-btn`);
        
        controls.forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const period = e.target.dataset.period;
                if (period && period !== this.currentPeriod) {
                    // Update active state
                    controls.forEach(b => b.classList.remove('active'));
                    e.target.classList.add('active');
                    
                    // Load new data
                    this.currentPeriod = period;
                    await this.loadData(period);
                }
            });
        });
    }

    // Load chart data from API
    async loadData(period = '30d') {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading();

        try {
            const params = new URLSearchParams({
                period,
                group_by: this.getGroupingByPeriod(period),
                ...CarScraping.state.currentFilters
            });

            const response = await fetch(`${CarScraping.api.charts}/price-trend?${params}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.updateChart(data);

        } catch (error) {
            console.error('Error loading price trend data:', error);
            this.showError('Errore nel caricamento del grafico trend prezzi');
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }

    // Update chart with new data
    updateChart(data) {
        if (!this.chart || !data) return;

        // Prepare datasets
        const datasets = this.prepareDatasets(data);
        
        // Update chart data
        this.chart.data.labels = data.dates;
        this.chart.data.datasets = datasets;
        
        // Add annotations for significant events
        if (data.events) {
            this.addEventAnnotations(data.events);
        }
        
        // Update chart
        this.chart.update('active');

        // Update statistics
        this.updateChartStatistics(data.statistics);
    }

    // Prepare chart datasets
    prepareDatasets(data) {
        const datasets = [
            {
                label: 'Prezzo Medio Generale',
                data: data.overall,
                borderColor: '#1e3a8a',
                backgroundColor: 'rgba(30, 58, 138, 0.1)',
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointBackgroundColor: '#1e3a8a',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                order: 1
            }
        ];

        // Add mileage-based datasets if available
        if (data.by_mileage) {
            datasets.push(
                {
                    label: '0-50.000 km',
                    data: data.by_mileage.low,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    order: 2
                },
                {
                    label: '50.000-100.000 km',
                    data: data.by_mileage.medium,
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    order: 3
                },
                {
                    label: '100.000+ km',
                    data: data.by_mileage.high,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    order: 4
                }
            );
        }

        // Add trend line if available
        if (data.trend_line) {
            datasets.push({
                label: 'Trend',
                data: data.trend_line,
                borderColor: '#6b7280',
                backgroundColor: 'transparent',
                borderWidth: 2,
                borderDash: [5, 5],
                tension: 0,
                fill: false,
                pointRadius: 0,
                pointHoverRadius: 0,
                order: 5
            });
        }

        return datasets;
    }

    // Add event annotations to chart
    addEventAnnotations(events) {
        if (!this.chart.options.plugins.annotation) {
            this.chart.options.plugins.annotation = { annotations: {} };
        }

        events.forEach((event, index) => {
            this.chart.options.plugins.annotation.annotations[`event-${index}`] = {
                type: 'line',
                scaleID: 'x',
                value: event.date,
                borderColor: '#f59e0b',
                borderWidth: 2,
                borderDash: [3, 3],
                label: {
                    content: event.label,
                    enabled: true,
                    position: 'top',
                    backgroundColor: 'rgba(245, 158, 11, 0.8)',
                    color: '#ffffff',
                    font: {
                        size: 10,
                        weight: 'bold'
                    },
                    padding: 4,
                    cornerRadius: 4
                }
            };
        });
    }

    // Update chart statistics display
    updateChartStatistics(statistics) {
        if (!statistics) return;

        // Update any statistics elements
        const statsElements = {
            'price-trend-avg': statistics.average,
            'price-trend-change': statistics.change_percentage,
            'price-trend-volatility': statistics.volatility
        };

        Object.entries(statsElements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element && value !== undefined) {
                element.textContent = this.formatStatistic(id, value);
            }
        });
    }

    // Format statistical values
    formatStatistic(type, value) {
        switch (type) {
            case 'price-trend-avg':
                return this.formatPrice(value);
            case 'price-trend-change':
                const sign = value >= 0 ? '+' : '';
                return `${sign}${value.toFixed(1)}%`;
            case 'price-trend-volatility':
                return `${value.toFixed(2)}%`;
            default:
                return value.toString();
        }
    }

    // Get grouping strategy based on period
    getGroupingByPeriod(period) {
        const groupingMap = {
            '7d': 'day',
            '30d': 'day',
            '90d': 'week',
            '1y': 'week',
            '2y': 'month'
        };
        return groupingMap[period] || 'day';
    }

    // Calculate price change percentage
    calculateChange(context) {
        const dataset = context.dataset;
        const currentIndex = context.dataIndex;
        
        if (currentIndex === 0 || !dataset.data[currentIndex - 1]) {
            return '';
        }

        const current = dataset.data[currentIndex];
        const previous = dataset.data[currentIndex - 1];
        const change = ((current - previous) / previous) * 100;
        
        const sign = change >= 0 ? '+' : '';
        const color = change >= 0 ? '#10b981' : '#ef4444';
        
        return ` (${sign}${change.toFixed(1)}%)`;
    }

    // Calculate trend direction
    calculateTrend(data, currentIndex) {
        if (currentIndex < 5) return 'Dati insufficienti';
        
        const recent = data.slice(Math.max(0, currentIndex - 4), currentIndex + 1);
        let increasing = 0;
        
        for (let i = 1; i < recent.length; i++) {
            if (recent[i] > recent[i - 1]) increasing++;
        }
        
        const ratio = increasing / (recent.length - 1);
        
        if (ratio >= 0.7) return '📈 In crescita';
        if (ratio <= 0.3) return '📉 In calo';
        return '➡️ Stabile';
    }

    // Show loading state
    showLoading() {
        const container = this.chart.canvas.parentElement;
        container.classList.add('loading');
    }

    // Hide loading state
    hideLoading() {
        const container = this.chart.canvas.parentElement;
        container.classList.remove('loading');
    }

    // Show error state
    showError(message) {
        console.error('Price trend chart error:', message);
        
        // You could show an error overlay here
        if (window.showToast) {
            window.showToast(message, 'error');
        }
    }

    // Format price with locale
    formatPrice(price) {
        if (!price || price === 0) return '€0';
        
        return new Intl.NumberFormat('it-IT', {
            style: 'currency',
            currency: 'EUR',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(price);
    }

    // Get zoom plugin configuration
    getZoomPlugin() {
        return {
            id: 'zoom',
            beforeInit: (chart) => {
                // Add zoom reset button
                this.addZoomResetButton(chart);
            }
        };
    }

    // Get annotation plugin configuration
    getAnnotationPlugin() {
        return {
            id: 'annotation'
        };
    }

    // Add zoom reset button
    addZoomResetButton(chart) {
        // This would add a reset zoom button to the chart controls
        // Implementation would depend on your UI framework
    }

    // Export chart data
    exportData(format = 'csv') {
        if (!this.chart.data) return;

        const data = this.chart.data;
        let content = '';

        if (format === 'csv') {
            // CSV format
            const headers = ['Data', ...data.datasets.map(d => d.label)];
            content = headers.join(',') + '\n';

            data.labels.forEach((label, index) => {
                const row = [label];
                data.datasets.forEach(dataset => {
                    row.push(dataset.data[index] || '');
                });
                content += row.join(',') + '\n';
            });
        }

        // Trigger download
        const blob = new Blob([content], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `price-trend-${this.currentPeriod}-${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    }

    // Destroy chart
    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }
}

// Export for global use
window.PriceTrendChart = PriceTrendChart;