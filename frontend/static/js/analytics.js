/* CrowdSafe - Analytics */

let personChart = null;
let densityChartA = null;
let riskChart = null;
let velocityChart = null;

let currentRange = '30d';
let customStart = null;
let customEnd = null;
let tableVisible = false;

/* ---------- Camera Loader ---------- */

async function loadCameraOptions() {
    try {
        const res = await apiFetch('/api/cameras');
        const cameras = await res.json();
        const sel = document.getElementById('cameraSelect');
        if (!sel) return;
        while (sel.options.length > 1) sel.remove(1);
        cameras.forEach(cam => {
            const opt = document.createElement('option');
            opt.value = cam.id;
            opt.textContent = cam.name || cam.id;
            sel.appendChild(opt);
        });
        if (cameras.length > 0 && !sel.value) {
            sel.value = cameras[0].id;
            loadAnalytics();
        }
    } catch { /* ignore */ }
}

/* ---------- Range Helpers ---------- */

function getDateRange() {
    if (customStart && customEnd) {
        return { start: customStart, end: customEnd };
    }
    const now = new Date();
    let start = null;
    switch (currentRange) {
        case '1h':  start = new Date(now - 3600 * 1000); break;
        case '24h': start = new Date(now - 86400 * 1000); break;
        case '7d':  start = new Date(now - 7 * 86400 * 1000); break;
        case '30d': start = new Date(now - 30 * 86400 * 1000); break;
        case 'all': return {};
    }
    return start ? { start: start.toISOString(), end: now.toISOString() } : {};
}

function selectRange(range) {
    currentRange = range;
    customStart = null;
    customEnd = null;
    document.getElementById('startDate').value = '';
    document.getElementById('endDate').value = '';
    document.querySelectorAll('.range-btn').forEach(b => b.classList.remove('active'));
    const active = document.querySelector(`.range-btn[data-range="${range}"]`);
    if (active) active.classList.add('active');
    loadAnalytics();
}

function applyCustomRange() {
    const s = document.getElementById('startDate').value;
    const e = document.getElementById('endDate').value;
    if (!s || !e) {
        if (typeof showToast === 'function') showToast('Select both start and end dates', 'warning');
        return;
    }
    customStart = new Date(s).toISOString();
    customEnd = new Date(e).toISOString();
    document.querySelectorAll('.range-btn').forEach(b => b.classList.remove('active'));
    loadAnalytics();
}

/* ---------- Main Load ---------- */

async function loadAnalytics() {
    const camId = document.getElementById('cameraSelect').value;
    if (!camId) return;

    const range = getDateRange();
    let params = new URLSearchParams();
    if (range.start) params.set('start', range.start);
    if (range.end) params.set('end', range.end);
    params.set('limit', '2000');

    const qs = params.toString();

    try {
        const [metricsRes, summaryRes] = await Promise.all([
            apiFetch('/api/metrics/' + camId + '?' + qs),
            apiFetch('/api/metrics/' + camId + '/summary?' + qs),
        ]);
        const metrics = await metricsRes.json();
        const summary = await summaryRes.json();

        updateSummary(summary);
        updateCharts(metrics);
        updateDataTable(metrics);
    } catch (err) {
        console.error('Analytics load error:', err);
    }
}

/* ---------- Summary ---------- */

function updateSummary(summary) {
    const el = (id, val) => {
        const e = document.getElementById(id);
        if (e) e.textContent = val;
    };
    el('sumAvgPeople', String(Math.round(summary.avg_count || 0)));
    el('sumMaxPeople', String(summary.peak_count || 0));
    el('sumAvgDensity', (summary.avg_density || 0).toFixed(2));
    el('sumMaxDensity', 'max: ' + (summary.max_density || 0).toFixed(2));
    el('sumMaxRisk', ((summary.max_risk_score || 0) * 100).toFixed(0) + '%');
    el('sumAvgRisk', 'avg: ' + ((summary.avg_risk || 0) * 100).toFixed(0) + '%');
    el('sumAvgVelocity', (summary.avg_velocity || 0).toFixed(2) + ' m/s');
    el('sumTotalRecords', String(summary.total_records || 0));
}

/* ---------- Charts ---------- */

function updateCharts(metrics) {
    const labels = metrics.map(m => {
        if (!m.timestamp) return '';
        return toISTTime(m.timestamp);
    });

    const counts = metrics.map(m => m.count || 0);
    const densities = metrics.map(m => m.density || 0);
    const risks = metrics.map(m => (m.risk_score || 0) * 100);
    const velocities = metrics.map(m => m.avg_velocity || 0);

    personChart = renderChart('personChart', personChart, 'Person Count', labels, counts, '#00d4ff');
    densityChartA = renderChart('densityChartA', densityChartA, 'Density (p/m\u00B2)', labels, densities, '#ff9500');
    riskChart = renderChart('riskChart', riskChart, 'Risk Score (%)', labels, risks, '#ff3b5c');
    velocityChart = renderChart('velocityChart', velocityChart, 'Velocity (m/s)', labels, velocities, '#00e676');
}

function renderChart(canvasId, existing, label, labels, data, color) {
    if (existing) {
        existing.data.labels = labels;
        existing.data.datasets[0].data = data;
        existing.update('none');
        return existing;
    }

    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: color,
                backgroundColor: color + '1a',
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                },
            },
            scales: {
                x: {
                    display: true,
                    grid: { color: 'rgba(255,255,255,0.03)' },
                    ticks: { color: '#64748b', font: { size: 9 }, maxTicksLimit: 12 },
                },
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#64748b', font: { size: 10 } },
                },
            },
            animation: false,
        },
    });
}

/* ---------- Data Table ---------- */

function toggleDataTable() {
    tableVisible = !tableVisible;
    document.getElementById('dataTableWrap').style.display = tableVisible ? '' : 'none';
    document.getElementById('tableToggleIcon').className = tableVisible ? 'bi bi-chevron-up' : 'bi bi-chevron-down';
}

function updateDataTable(metrics) {
    const tbody = document.getElementById('dataTableBody');
    if (!tbody) return;

    // Clear existing rows
    while (tbody.firstChild) tbody.removeChild(tbody.firstChild);

    if (!metrics || metrics.length === 0) {
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = 7;
        td.className = 'text-center text-secondary py-3';
        td.textContent = 'No data for selected range';
        tr.appendChild(td);
        tbody.appendChild(tr);
        return;
    }

    const levelColors = {
        'CRITICAL': '#ff3b5c',
        'WARNING': '#ff9500',
        'CAUTION': '#ffd60a',
        'SAFE': '#00e676',
    };

    // Show most recent first in table
    const sorted = [...metrics].reverse();

    sorted.forEach(m => {
        const tr = document.createElement('tr');

        const tdTs = document.createElement('td');
        tdTs.className = 'small';
        tdTs.textContent = m.timestamp ? toIST(m.timestamp) : '-';
        tr.appendChild(tdTs);

        const tdCount = document.createElement('td');
        tdCount.textContent = String(m.count || 0);
        tr.appendChild(tdCount);

        const tdDensity = document.createElement('td');
        tdDensity.textContent = (m.density || 0).toFixed(2);
        tr.appendChild(tdDensity);

        const tdVelocity = document.createElement('td');
        tdVelocity.textContent = (m.avg_velocity || 0).toFixed(2);
        tr.appendChild(tdVelocity);

        const tdSurge = document.createElement('td');
        tdSurge.textContent = (m.surge_rate || 0).toFixed(3);
        tr.appendChild(tdSurge);

        const tdRisk = document.createElement('td');
        tdRisk.textContent = ((m.risk_score || 0) * 100).toFixed(1) + '%';
        tr.appendChild(tdRisk);

        const tdLevel = document.createElement('td');
        const badge = document.createElement('span');
        badge.className = 'badge';
        badge.style.background = levelColors[m.risk_level] || '#64748b';
        badge.style.color = '#000';
        badge.style.fontSize = '0.7rem';
        badge.textContent = m.risk_level || 'SAFE';
        tdLevel.appendChild(badge);
        tr.appendChild(tdLevel);

        tbody.appendChild(tr);
    });
}

/* ---------- Export ---------- */

function exportData(format) {
    const camId = document.getElementById('cameraSelect').value;
    if (!camId) {
        if (typeof showToast === 'function') showToast('Select a camera first', 'warning');
        return;
    }

    const range = getDateRange();
    let params = new URLSearchParams();
    params.set('format', format);
    if (range.start) params.set('start', range.start);
    if (range.end) params.set('end', range.end);

    const token = localStorage.getItem('access_token');
    const url = '/api/metrics/' + camId + '/export?' + params.toString();

    fetch(url, {
        headers: token ? { 'Authorization': 'Bearer ' + token } : {}
    })
    .then(res => {
        if (!res.ok) throw new Error('Export failed');
        const disposition = res.headers.get('Content-Disposition') || '';
        let filename = 'crowdsafe_export.' + format;
        const match = disposition.match(/filename="?(.+?)"?$/);
        if (match) filename = match[1];
        return res.blob().then(blob => ({ blob, filename }));
    })
    .then(({ blob, filename }) => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(a.href);
        if (typeof showToast === 'function') showToast('Exported ' + format.toUpperCase(), 'success');
    })
    .catch(err => {
        console.error('Export error:', err);
        if (typeof showToast === 'function') showToast('Export failed', 'danger');
    });
}

/* ---------- Init ---------- */

document.addEventListener('DOMContentLoaded', () => {
    loadCameraOptions();

    // Range button listeners
    document.querySelectorAll('.range-btn').forEach(btn => {
        btn.addEventListener('click', () => selectRange(btn.dataset.range));
    });

    // Camera change
    const camSel = document.getElementById('cameraSelect');
    if (camSel) camSel.addEventListener('change', loadAnalytics);
});
