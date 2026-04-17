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
        btn.classList.toggle('btn-outline-info', !heatmapOn);
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
        if (data.recording_id) {
            showDownloadButton(data.recording_id);
        }
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
    setMetric('metricPeople', String(m.count || 0));
    setMetric('metricDensity', (m.density || 0).toFixed(2) + ' p/m\u00B2');
    setMetric('metricVelocity', (m.avg_velocity || 0).toFixed(2) + ' m/s');
    setMetric('metricSurge', (m.surge_rate || 0).toFixed(2));
    setMetric('metricCapacity', (m.capacity_utilization || 0).toFixed(0) + '%');
    setMetric('metricRiskScore', ((m.risk_score || 0) * 100).toFixed(0) + '%');

    const levelEl = document.getElementById('metricRiskLevel');
    if (levelEl) {
        levelEl.textContent = m.risk_level || 'SAFE';
        levelEl.className = 'text-end fw-bold ' + riskClass(m.risk_level);
    }

    // ML metrics
    setMetric('metricClusters', String(m.num_clusters || 0));
    setMetric('metricCoherence', (m.flow_coherence || 0).toFixed(2));
    setMetric('metricPressure', (m.crowd_pressure || 0).toFixed(2));
    setMetric('metricAnomalies', String(m.num_anomalies || 0));

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

    // Update chart
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
                borderColor: '#4f8ff7',
                backgroundColor: 'rgba(79, 143, 247, 0.1)',
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { display: false },
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

function setupCameraSocket() {
    if (!CS.socket) return;
    CS.socket.emit('subscribe_camera', { camera_id: CAMERA_ID });
    CS.socket.on('metrics_update', (data) => {
        if (data.camera_id === CAMERA_ID) {
            updateMetrics(data);
        }
    });
    CS.socket.on('camera_status', (data) => {
        if (data.camera_id === CAMERA_ID && data.recording_id) {
            showDownloadButton(data.recording_id);
        }
    });
}

/* ---------- Init ---------- */
document.addEventListener('DOMContentLoaded', () => {
    initDensityChart();
    loadCameraInfo();
    setupCameraSocket();
});
