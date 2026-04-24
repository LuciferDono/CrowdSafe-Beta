/* CrowdSafe - Camera View */
/* CAMERA_ID is set in template via <script>const CAMERA_ID = "...";</script> */

let densityChart = null;
let densityData = [];
const MAX_POINTS = 60;
let heatmapOn = false;
let lastRecordingId = null;

async function loadCameraInfo() {
    try {
        const res = await apiFetch('/api/cameras/' + CAMERA_ID);
        const cam = await res.json();
        const nameEl = document.getElementById('cameraName');
        const statusEl = document.getElementById('cameraStatus');
        if (nameEl) nameEl.textContent = cam.name || CAMERA_ID;
        if (statusEl) {
            statusEl.textContent = cam.is_processing ? 'LIVE' : cam.status || 'offline';
            statusEl.className = 'badge ' + (cam.is_processing ? 'bg-processing' : 'bg-offline');
        }
        startStream(cam.is_processing);
    } catch { /* ignore */ }
}

function startStream(isProcessing) {
    const feed = document.getElementById('videoFeed');
    const overlay = document.getElementById('videoOverlay');
    if (!feed) return;
    if (isProcessing) {
        feed.src = '/api/cameras/' + CAMERA_ID + '/stream' + (heatmapOn ? '?heatmap=1' : '');
        feed.style.display = '';
        if (overlay) overlay.classList.add('d-none');
    } else {
        feed.style.display = 'none';
        if (overlay) overlay.classList.remove('d-none');
    }
}

function toggleHeatmap() {
    heatmapOn = !heatmapOn;
    const btn = document.getElementById('btnHeatmap');
    if (btn) {
        btn.classList.toggle('btn-info', heatmapOn);
        btn.classList.toggle('btn-outline-secondary', !heatmapOn);
    }
    const feed = document.getElementById('videoFeed');
    if (feed && feed.style.display !== 'none') {
        feed.src = '/api/cameras/' + CAMERA_ID + '/stream' + (heatmapOn ? '?heatmap=1' : '');
    }
}

async function stopCamera() {
    try {
        const res = await apiFetch('/api/cameras/' + CAMERA_ID + '/stop', { method: 'POST' });
        const data = await res.json();
        if (data.recording_id) showDownloadButton(data.recording_id);
        loadCameraInfo();
    } catch { /* ignore */ }
}

function showDownloadButton(recordingId) {
    lastRecordingId = recordingId;
    const btn = document.getElementById('btnDownload');
    if (btn) btn.classList.remove('d-none');
}

function downloadRecording() {
    if (!lastRecordingId) return;
    window.location.href = '/api/recordings/' + lastRecordingId + '/download';
}

function updateMetrics(m) {
    // Hero stats
    setMetric('metricPeople', String(m.count || 0));
    setMetric('metricDensity', (m.density || 0).toFixed(2));
    setMetric('metricCapacity', (m.capacity_utilization || 0).toFixed(0) + '%');

    // Risk level — big coloured hero
    const levelEl = document.getElementById('metricRiskLevel');
    if (levelEl) {
        levelEl.textContent = m.risk_level || 'SAFE';
        levelEl.className = 'fw-bold ' + riskClass(m.risk_level);
    }
    setMetric('metricRiskScoreLabel', 'Score: ' + ((m.risk_score || 0) * 100).toFixed(0) + '%');

    // Motion stats
    setMetric('metricVelocity', (m.avg_velocity || 0).toFixed(2) + ' m/s');
    setMetric('metricSurge', (m.surge_rate || 0).toFixed(2));

    const dTrend = document.getElementById('metricDensityTrend');
    if (dTrend) {
        dTrend.textContent = m.density_trend || 'stable';
        dTrend.className = 'text-end fw-bold ' + trendClass(m.density_trend);
    }
    const rTrend = document.getElementById('metricRiskTrend');
    if (rTrend) {
        rTrend.textContent = m.risk_trend || 'stable';
        rTrend.className = 'text-end fw-bold ' + trendClass(m.risk_trend);
    }

    // ML metrics
    setMetric('metricClusters', String(m.num_clusters || 0));
    setMetric('metricCoherence', (m.flow_coherence || 0).toFixed(2));
    setMetric('metricPressure', (m.crowd_pressure || 0).toFixed(2));
    setMetric('metricAnomalies', String(m.num_anomalies || 0));

    // Density trend chart
    densityData.push(m.density || 0);
    if (densityData.length > MAX_POINTS) densityData.shift();
    if (densityChart) {
        densityChart.data.labels = densityData.map((_, i) => String(i));
        densityChart.data.datasets[0].data = densityData;
        densityChart.update('none');
    }
}

function trendClass(trend) {
    if (trend === 'increasing') return 'text-danger';
    if (trend === 'decreasing') return 'text-success';
    return 'text-secondary';
}

function setMetric(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}

function initDensityChart() {
    const ctx = document.getElementById('densityChart');
    if (!ctx) return;
    densityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Density',
                data: [],
                borderColor: '#06b6d4',
                backgroundColor: 'rgba(6, 182, 212, 0.08)',
                fill: true,
                tension: 0.35,
                pointRadius: 0,
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { display: false },
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.04)' },
                    ticks: { color: '#64748b', font: { size: 10 } },
                },
            },
            animation: false,
        },
    });
}

function setupCameraSocket() {
    if (!CS.socket) return;
    CS.socket.emit('subscribe_camera', { camera_id: CAMERA_ID });
    CS.socket.on('metrics_update', (data) => {
        if (data.camera_id === CAMERA_ID) updateMetrics(data);
    });
    CS.socket.on('camera_status', (data) => {
        if (data.camera_id === CAMERA_ID && data.recording_id) showDownloadButton(data.recording_id);
    });
}

/* ---------- Popular Times ---------- */
let popularTimesChart = null;

async function loadPopularTimes() {
    try {
        const res = await apiFetch('/api/cameras/' + CAMERA_ID + '/popular-times');
        if (!res.ok) return;
        renderPopularTimes(await res.json());
    } catch { /* ignore */ }
}

function renderPopularTimes(data) {
    if (!data || !data.hours || data.hours.length === 0) return;

    const display = data.hours.filter(h => h.hour >= 6 && h.hour <= 23);
    const currentHour = new Date().getHours();

    const labels      = display.map(h => h.label);
    const intensities = display.map(h => h.has_data ? h.relative_intensity : 0);

    const bgColors = display.map(h => {
        if (h.hour === currentHour) return 'rgba(250, 220, 80, 0.90)';
        if (!h.has_data)            return 'rgba(148, 163, 184, 0.10)';
        const i = h.relative_intensity;
        if (i < 0.33) return 'rgba(16, 185, 129, 0.72)';
        if (i < 0.66) return 'rgba(234, 179,   8, 0.78)';
        return              'rgba(239,  68,  68, 0.82)';
    });

    const borderColors = display.map(h =>
        h.hour === currentHour ? 'rgba(250, 220, 80, 1)' : 'transparent'
    );
    const borderWidths = display.map(h => h.hour === currentHour ? 2 : 0);

    const ctx = document.getElementById('popularTimesChart');
    if (!ctx) return;

    if (popularTimesChart) popularTimesChart.destroy();
    popularTimesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                data:            intensities,
                backgroundColor: bgColors,
                borderColor:     borderColors,
                borderWidth:     borderWidths,
                borderRadius:    5,
                borderSkipped:   false,
            }],
        },
        options: {
            responsive:          true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: (items) => {
                            const h = display[items[0].dataIndex];
                            return h.hour === currentHour ? h.label + '  (Now)' : h.label;
                        },
                        label: (item) => {
                            const h = display[item.dataIndex];
                            if (!h.has_data) return 'No historical data';
                            const busy = h.relative_intensity < 0.33 ? 'Usually not busy'
                                       : h.relative_intensity < 0.66 ? 'Usually a little busy'
                                       : 'Usually very busy';
                            return [
                                busy,
                                `Avg crowd: ~${Math.round(h.avg_count)} people`,
                                `Density: ${h.avg_density.toFixed(2)} p/m²`,
                            ];
                        },
                    },
                },
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: {
                        color:       '#64748b',
                        font:        { size: 10 },
                        maxRotation: 0,
                        callback:    (_v, idx) => idx % 2 === 0 ? labels[idx] : '',
                    },
                },
                y: { display: false, beginAtZero: true, max: 1 },
            },
            animation: { duration: 500 },
        },
    });

    // Peak label — backend now guarantees peak_hour is within 6–23
    const peakEl = document.getElementById('popularPeakLabel');
    if (peakEl && data.peak_hour !== null) {
        const peak = data.hours[data.peak_hour];
        peakEl.textContent = peak
            ? `Peak: ${peak.label}  ·  ~${Math.round(peak.avg_count)} people`
            : '';
    }

    const metaEl = document.getElementById('popularTimesMeta');
    if (metaEl) {
        metaEl.textContent = `${data.total_samples} data point${data.total_samples === 1 ? '' : 's'} recorded`;
    }
}

/* ---------- Init ---------- */
document.addEventListener('DOMContentLoaded', () => {
    initDensityChart();
    loadCameraInfo();
    setupCameraSocket();
    loadPopularTimes();
});
