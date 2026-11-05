(() => {
    const palette = ['#7062dd', '#4e94e8', '#38b5a4', '#edae4d', '#e87891', '#8c80df', '#74b2bd'];
    const currency = (value) => `₹${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
    const readData = (id) => {
        const element = document.getElementById(id);
        return element ? JSON.parse(element.textContent) : null;
    };

    const monthlyData = readData('monthly-chart-data');
    const monthlyCanvas = document.getElementById('monthlyExpensesChart');
    if (monthlyData && monthlyCanvas && window.Chart) {
        const barTrackPlugin = {
            id: 'smartSpendBarTracks',
            beforeDatasetsDraw(chart) {
                const meta = chart.getDatasetMeta(0);
                if (!meta.data.length) return;
                const { ctx, chartArea } = chart;
                ctx.save();
                ctx.fillStyle = '#efedfa';
                meta.data.forEach((bar) => {
                    const width = Math.max(bar.width * 0.72, 8);
                    const radius = Math.min(width / 2, 7);
                    const x = bar.x - width / 2;
                    const y = chartArea.top;
                    const height = chartArea.bottom - chartArea.top;
                    ctx.beginPath();
                    ctx.moveTo(x + radius, y);
                    ctx.lineTo(x + width - radius, y);
                    ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
                    ctx.lineTo(x + width, y + height - radius);
                    ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
                    ctx.lineTo(x + radius, y + height);
                    ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
                    ctx.lineTo(x, y + radius);
                    ctx.quadraticCurveTo(x, y, x + radius, y);
                    ctx.closePath();
                    ctx.fill();
                });
                ctx.restore();
            },
        };

        new Chart(monthlyCanvas, {
            type: 'bar',
            data: {
                labels: monthlyData.labels,
                datasets: [{
                    label: 'Expenses',
                    data: monthlyData.values,
                    backgroundColor: '#7669e8',
                    hoverBackgroundColor: '#5e52d0',
                    borderRadius: 7,
                    borderSkipped: false,
                    maxBarThickness: 34,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 650 },
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: (context) => ` ${currency(context.parsed.y)}` } },
                },
                scales: {
                    x: {
                        grid: { display: false },
                        border: { display: false },
                        ticks: { color: '#969bad', font: { size: 10, family: 'Inter, sans-serif' } },
                    },
                    y: {
                        beginAtZero: true,
                        border: { display: false, dash: [3, 4] },
                        grid: { color: '#f0f1f6', drawTicks: false },
                        ticks: {
                            color: '#a0a5b4',
                            padding: 10,
                            maxTicksLimit: 5,
                            font: { size: 9, family: 'Inter, sans-serif' },
                            callback: (value) => currency(value),
                        },
                    },
                },
            },
            plugins: [barTrackPlugin],
        });
    }

    const investmentData = readData('investment-chart-data');
    const investmentCanvas = document.getElementById('investmentSparkline');
    if (investmentData && investmentCanvas && window.Chart) {
        new Chart(investmentCanvas, {
            type: 'line',
            data: {
                labels: investmentData.labels,
                datasets: [{
                    data: investmentData.values,
                    borderColor: '#8174e8',
                    backgroundColor: 'rgba(129, 116, 232, .10)',
                    borderWidth: 2,
                    fill: true,
                    tension: .42,
                    pointRadius: 0,
                    pointHitRadius: 0,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 600 },
                plugins: { legend: { display: false }, tooltip: { enabled: false } },
                scales: { x: { display: false }, y: { display: false, beginAtZero: true } },
                elements: { line: { capBezierPoints: true } },
            },
        });
    }

    const categoryData = readData('category-chart-data');
    const categoryCanvas = document.getElementById('expenseCategoryChart');
    if (categoryData && categoryCanvas && window.Chart) {
        new Chart(categoryCanvas, {
            type: 'doughnut',
            data: {
                labels: categoryData.labels,
                datasets: [{
                    data: categoryData.values,
                    backgroundColor: categoryData.labels.map((_, index) => palette[index % palette.length]),
                    hoverOffset: 5,
                    borderColor: '#ffffff',
                    borderWidth: 4,
                    borderRadius: 4,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '72%',
                animation: { duration: 650 },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => ` ${context.label}: ${currency(context.parsed)}`,
                        },
                    },
                },
            },
        });

        const legend = document.getElementById('categoryChartLegend');
        if (legend) {
            categoryData.labels.forEach((label, index) => {
                const row = document.createElement('li');
                const dot = document.createElement('span');
                dot.className = 'legend-dot';
                dot.style.backgroundColor = palette[index % palette.length];
                const name = document.createElement('span');
                name.className = 'legend-name';
                name.textContent = label;
                const amount = document.createElement('span');
                amount.className = 'legend-value';
                amount.textContent = currency(categoryData.values[index]);
                row.append(dot, name, amount);
                legend.append(row);
            });
        }
    }
})();
