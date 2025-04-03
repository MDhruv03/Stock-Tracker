// portfolio.js - Complete Fixed Version

// ======================
// Configuration
// ======================
const config = {
    baseUrl: document.querySelector('meta[name="base-url"]')?.content || window.location.origin,
    endpoints: {
        allocations: '/portfolio/allocation',
        history: '/portfolio/history',
        transactions: '/portfolio/transactions_history'
    }
};

// Debugging
console.log("Base URL:", config.baseUrl);

// ======================
// DOM Elements
// ======================
const elements = {
    allocationBtn: document.getElementById("allocation-btn"),
    allocationContainer: document.getElementById("allocation-container"),
    allocationResults: document.getElementById("allocation-results"),
    portfolioGraph: document.getElementById("portfolioGraph"),
    toggleTransactions: document.getElementById("toggle-transactions"),
    transactionHistory: document.getElementById("transaction-history"),
    transactionTableBody: document.getElementById("transaction-table-body")
};

// Verify elements exist
console.log("DOM Elements:", elements);

// ======================
// Utility Functions
// ======================
const utils = {
    showLoading: (element) => {
        if (element) element.classList.add("loading");
    },
    hideLoading: (element) => {
        if (element) element.classList.remove("loading");
    },
    showError: (element, message) => {
        if (element) element.innerHTML = `<div class="error-message">${message}</div>`;
    },
    formatCurrency: (amount) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 2
        }).format(amount).replace('₹', '₹');
    }
};

// ======================
// API Functions
// ======================
const api = {
    fetchAllocations: async () => {
        try {
            const response = await fetch(`${config.baseUrl}${config.endpoints.allocations}`, {
                credentials: 'include'
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to fetch allocations');
            }
            return await response.json();
        } catch (error) {
            console.error("Allocations API Error:", error);
            throw error;
        }
    },
    
    fetchPortfolioHistory: async () => {
        try {
            const response = await fetch(`${config.baseUrl}${config.endpoints.history}`, {
                credentials: 'include'
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to fetch portfolio history');
            }
            const data = await response.json();
            console.log("Portfolio History Data:", data);
            return data;
        } catch (error) {
            console.error("History API Error:", error);
            throw error;
        }
    },
    
    fetchTransactions: async () => {
        try {
            const response = await fetch(`${config.baseUrl}${config.endpoints.transactions}`, {
                credentials: 'include'
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to fetch transactions');
            }
            return await response.json();
        } catch (error) {
            console.error("Transactions API Error:", error);
            throw error;
        }
    }
};

// ======================
// Chart Functions
// ======================
const chart = {
    init: async () => {
        console.log("Initializing chart...");
        if (!elements.portfolioGraph) {
            console.error("Chart canvas element not found");
            return;
        }

        try {
            const data = await api.fetchPortfolioHistory();
            console.log("Chart data received:", data);
            
            if (!data?.history?.length) {
                console.warn("No historical data available");
                elements.portfolioGraph.outerHTML = `
                    <div class="no-data">
                        No historical data available
                    </div>
                `;
                return;
            }
            
            const dates = data.history.map(entry => entry.date);
            const values = data.history.map(entry => entry.portfolio_value);
            
            // Destroy previous chart if exists
            if (elements.portfolioGraph.chart) {
                elements.portfolioGraph.chart.destroy();
            }
            
            // Create new chart
            elements.portfolioGraph.chart = new Chart(
                elements.portfolioGraph.getContext('2d'),
                chart.getConfig(dates, values)
            );
            
            console.log("Chart initialized successfully");
        } catch (error) {
            console.error("Chart initialization failed:", error);
            if (elements.portfolioGraph) {
                elements.portfolioGraph.outerHTML = `
                    <div class="error-message">
                        Error loading chart: ${error.message}
                    </div>
                `;
            }
        }
    },
    
    getConfig: (labels, data) => ({
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Portfolio Value (₹)",
                data: data,
                borderColor: "var(--primary)",
                backgroundColor: "rgba(0, 255, 157, 0.1)",
                borderWidth: 2,
                pointRadius: 0,  // Changed from 3 to 0 to match stock details
                pointBackgroundColor: "var(--primary)",
                pointHoverRadius: 5,
                fill: true,
                tension: 0.1  // Changed from 0.4 to 0.1 to match stock details
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { 
                    display: false 
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: "var(--card-bg)",
                    titleColor: "var(--text)",
                    bodyColor: "var(--text)",  // Changed from primary to text
                    borderColor: "var(--border)",
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: (context) => `₹${context.parsed.y.toFixed(2)}`
                    }
                },
                zoom: {  // Added zoom plugin to match stock details
                    zoom: {
                        wheel: {
                            enabled: true,
                        },
                        pinch: {
                            enabled: true
                        },
                        mode: 'x',
                    },
                    pan: {
                        enabled: true,
                        mode: 'x',
                    }
                }
            },
            scales: {
                x: {
                    grid: { 
                        color: "var(--border)",  // Changed from rgba to CSS variable
                        drawBorder: false
                    },
                    ticks: { 
                        color: "#ffffff",
                        font: {
                            size: 11
                        }
                    }
                },
                y: {
                    beginAtZero: false,  // Added to match stock details
                    grid: { 
                        color: "var(--border)",  // Changed from rgba to CSS variable
                        drawBorder: false
                    },
                    ticks: {
                        color: "#ffffff",
                        font: {
                            size: 11
                        },
                        callback: (value) => `₹${value}`
                    }
                }
            },
            interaction: {  // Added interaction settings to match stock details
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    })
};


const ui = {
    initAllocationButton: () => {
        if (!elements.allocationBtn) return;
        
        elements.allocationBtn.addEventListener("click", async () => {
            if (!elements.allocationContainer) return;
            
            elements.allocationContainer.classList.toggle("show");
            
            if (elements.allocationContainer.classList.contains("show")) {
                try {
                    utils.showLoading(elements.allocationContainer);
                    const data = await api.fetchAllocations();
                    
                    let html = `
                        <table>
                            <thead>
                                <tr>
                                    <th>Stock</th>
                                    <th>Allocation %</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;
                    
                    data.forEach(item => {
                        html += `
                            <tr>
                                <td>${item.stock_ticker || item.stock_id}</td>
                                <td>${item.allocation_percentage}%</td>
                            </tr>
                        `;
                    });
                    
                    html += `</tbody></table>`;
                    if (elements.allocationResults) {
                        elements.allocationResults.innerHTML = html;
                    }
                    
                } catch (error) {
                    console.error("Allocation error:", error);
                    if (elements.allocationResults) {
                        utils.showError(elements.allocationResults, 
                            `Error loading allocations: ${error.message}`);
                    }
                } finally {
                    utils.hideLoading(elements.allocationContainer);
                }
            }
        });
    },
    
    initTransactions: () => {
        if (!elements.toggleTransactions || !elements.transactionHistory) return;
        
        elements.toggleTransactions.addEventListener("click", () => {
            elements.transactionHistory.classList.toggle("show");
            const arrow = elements.toggleTransactions.querySelector('div');
            if (arrow) {
                arrow.textContent = elements.transactionHistory.classList.contains("show") 
                    ? "▲" 
                    : "▼";
            }
            
            if (elements.transactionHistory.classList.contains("show")) {
                ui.loadTransactions();
            }
        });
    },
    
    loadTransactions: async () => {
        if (!elements.transactionTableBody) return;
        
        try {
            elements.transactionTableBody.innerHTML = `
                <tr>
                    <td colspan="8" class="loading-state">
                        Loading transactions...
                    </td>
                </tr>
            `;
            
            const data = await api.fetchTransactions();
            console.log("Transactions data:", data);
            
            if (!data?.length) {
                elements.transactionTableBody.innerHTML = `
                    <tr>
                        <td colspan="8" class="no-data">
                            No transactions found
                        </td>
                    </tr>
                `;
                return;
            }
            
            elements.transactionTableBody.innerHTML = data.map(tx => `
                <tr>
                    <td>${tx.date}</td>
                    <td>${tx.stock_ticker}</td>
                    <td>${tx.type}</td>
                    <td>${tx.quantity}</td>
                    <td>${utils.formatCurrency(tx.price)}</td>
                    <td>${utils.formatCurrency(tx.transaction_amount)}</td>
                    <td class="${tx.realized_pnl >= 0 ? 'profit' : 'loss'}">
                        ${utils.formatCurrency(tx.realized_pnl)}
                    </td>
                    <td class="${tx.unrealized_pnl >= 0 ? 'profit' : 'loss'}">
                        ${utils.formatCurrency(tx.unrealized_pnl)}
                    </td>
                </tr>
            `).join('');
            
        } catch (error) {
            console.error("Transaction load error:", error);
            elements.transactionTableBody.innerHTML = `
                <tr>
                    <td colspan="8" class="error-message">
                        Error loading transactions: ${error.message}
                    </td>
                </tr>
            `;
        }
    },
    
    initButtonAnimations: () => {
        document.querySelectorAll('.btn').forEach(btn => {
            btn.addEventListener('click', function() {
                this.classList.add('animate__animated', 'animate__pulse');
                setTimeout(() => {
                    this.classList.remove('animate__animated', 'animate__pulse');
                }, 500);
            });
        });
    }
};

// ======================
// Initialization
// ======================
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM fully loaded, initializing components");
    
    // Initialize all components
    ui.initAllocationButton();
    ui.initTransactions();
    ui.initButtonAnimations();
    
    // Initialize chart
    chart.init();
    
    console.log("Initialization complete");
});