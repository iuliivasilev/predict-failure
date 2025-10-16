function createFeatureChart(chartData, selectedFeature){
    if (chartData) {
        const ctx = document.getElementById('featureChart').getContext('2d');
        const data = {
            labels: chartData.timestamps.map(ts => {
                const d = new Date(ts * 1000);
                return d.toLocaleString();
            }),
            datasets: [{
                label: selectedFeature,
                data: chartData.values,
                borderColor: '#7ecfff',
                backgroundColor: 'rgba(126,207,255,0.2)',
                tension: 0.2,
                pointRadius: 2,
            }]
        };
        new Chart(ctx, {
            type: 'line',
            data: data,
            options: {
                responsive: true,
                plugins: {
                    legend: { labels: { color: '#eee' } }
                },
                scales: {
                    x: { ticks: { color: '#eee' } },
                    y: { ticks: { color: '#eee' } }
                }
            }
        });
    }
}

// Автоматически строим график при загрузке страницы
if (typeof chartData !== 'undefined' && typeof selectedFeature !== 'undefined') {
    createFeatureChart(chartData, selectedFeature);
}