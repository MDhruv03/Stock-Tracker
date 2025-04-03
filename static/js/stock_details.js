let priceChart;
        
        document.addEventListener("DOMContentLoaded", function() {
            const ctx = document.getElementById('priceChart').getContext('2d');
            const chartData = {
                labels: JSON.parse('{{ chart_data.dates | tojson | safe }}'),
                datasets: [{
                    label: "Price (₹)",
                    data: JSON.parse('{{ chart_data.prices | tojson | safe }}'),
                    borderColor: 'var(--primary)',
                    backgroundColor: 'rgba(0, 255, 157, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: true,
                    tension: 0.1
                }]
            };

            priceChart = new Chart(ctx, {
                type: 'line',
                data: chartData,
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
                            bodyColor: "var(--text)",
                            borderColor: "var(--border)",
                            borderWidth: 1,
                            padding: 12,
                            callbacks: {
                                label: function(context) {
                                    return '₹' + context.parsed.y.toFixed(2);
                                }
                            }
                        },
                        zoom: {
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
                                color: "var(--border)"
                            },
                            ticks: {
                                color: "var(--text-secondary)"
                            }
                        },
                        y: {
                            beginAtZero: false,
                            grid: {
                                color: "var(--border)"
                            },
                            ticks: {
                                color: "var(--text-secondary)",
                                callback: function(value) {
                                    return '₹' + value;
                                }
                            }
                        }
                    },
                    interaction: {
                        mode: 'nearest',
                        axis: 'x',
                        intersect: false
                    }
                }
            });
            
            // Add animation to buttons on click
            document.querySelectorAll('.btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    this.classList.add('animate__animated', 'animate__pulse');
                    setTimeout(() => {
                        this.classList.remove('animate__animated', 'animate__pulse');
                    }, 500);
                });
            });
        });

        // Update chart timeframe
        function updateChart(timeframe) {
            // Update active button
            document.querySelectorAll('.timeframe-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // Show loading state
            priceChart.data.datasets[0].data = [];
            priceChart.update();
            
            // In a real app, you would fetch new data for the selected timeframe
            console.log("Loading data for timeframe:", timeframe);
            
            // Simulate loading
            setTimeout(() => {
                // This would be replaced with actual data fetching
                priceChart.update();
            }, 800);
        }
        
        // Toggle financials view
        function showFinancials(type) {
            document.querySelectorAll('.timeframe-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            if (type === 'yearly') {
                document.getElementById('yearly-financials').style.display = 'block';
                document.getElementById('quarterly-financials').style.display = 'none';
            } else {
                document.getElementById('yearly-financials').style.display = 'none';
                document.getElementById('quarterly-financials').style.display = 'block';
            }
        }
        
        // Placeholder functions for actions
        function showBuyForm() {
            alert("Buy form would appear here for " + '{{ stock.ticker }}');
        }
        
        function showAnalysis() {
            alert("Advanced analysis would appear here for " + '{{ stock.ticker }}');
        }