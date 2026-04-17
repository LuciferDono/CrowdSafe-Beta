/* CrowdSafe - Dashboard */

async function loadDashboard() {
    await Promise.all([loadStats(), loadCameraGrid(), loadAlertFeed()]);
}

async function loadStats() {
    try {
        const res = await apiFetch('/api/metrics/summary');
        const d = await res.json();
        setText('totalPeople', String(d.total_people || 0));
        setText('activeCameras', String(d.cameras_active || 0));
        const riskEl = document.getElementById('maxRisk');
        if (riskEl) {
            riskEl.textContent = d.max_risk_level || 'SAFE';
            riskEl.className = 'stat-value ' + riskClass(d.max_risk_level);
        }
    } catch { /* ignore */ }

    try {
        const res2 = await apiFetch('/api/alerts/unacknowledged/count');
        const d2 = await res2.json();
        setText('unackAlerts', String(d2.count || 0));
    } catch { /* ignore */ }

    try {
        const res3 = await apiFetch('/api/system/stats');
        const d3 = await res3.json();
        setText('statCamTotal', String(d3.cameras_total || 0));
        setText('statMetrics', String(d3.metrics_recorded || 0));
    } catch { /* ignore */ }
}

async function loadCameraGrid() {
    const grid = document.getElementById('cameraGrid');
    const empty = document.getElementById('emptyState');
    if (!grid) return;

    try {
        const res = await apiFetch('/api/cameras');
        const cameras = await res.json();
        const active = cameras.filter(c => c.is_processing);

        if (active.length === 0) {
            if (empty) empty.style.display = '';
            return;
        }
        if (empty) empty.style.display = 'none';

        const existingTiles = grid.querySelectorAll('.cam-tile-wrap');
        const activeIds = new Set(active.map(c => c.id));
        existingTiles.forEach(t => { if (!activeIds.has(t.dataset.camId)) t.remove(); });

        active.forEach(cam => {
            let wrap = grid.querySelector('[data-cam-id="' + cam.id + '"]');
            if (!wrap) {
                wrap = document.createElement('div');
                wrap.className = 'col-md-6 col-xl-4 cam-tile-wrap';
                wrap.dataset.camId = cam.id;

                const tile = document.createElement('div');
                tile.className = 'camera-tile';
                tile.addEventListener('click', () => { window.location.href = '/camera/' + cam.id; });

                const img = document.createElement('img');
                img.className = 'camera-thumb';
                img.alt = cam.name || cam.id;
                img.src = '/api/cameras/' + cam.id + '/stream';

                const info = document.createElement('div');
                info.className = 'camera-tile-info';
                const name = document.createElement('span');
                name.textContent = cam.name || cam.id;
                const meta = document.createElement('span');
                meta.className = 'camera-tile-meta tile-meta';
                info.appendChild(name);
                info.appendChild(meta);

                tile.appendChild(img);
                tile.appendChild(info);
                wrap.appendChild(tile);
                grid.appendChild(wrap);
            }
            const meta = wrap.querySelector('.tile-meta');
            if (meta && cam.current_metrics) {
                meta.textContent = (cam.current_metrics.count || 0) + ' people | ' + (cam.current_metrics.risk_level || 'SAFE');
            }
        });
    } catch { /* ignore */ }
}

async function loadAlertFeed() {
    const feed = document.getElementById('alertFeed');
    if (!feed) return;
    try {
        const res = await apiFetch('/api/alerts?limit=10');
        const alerts = await res.json();
        while (feed.firstChild) feed.removeChild(feed.firstChild);

        if (alerts.length === 0) {
            const p = document.createElement('p');
            p.className = 'text-secondary small text-center mb-0';
            p.textContent = 'No recent alerts';
            feed.appendChild(p);
            return;
        }
        alerts.forEach(a => {
            const item = document.createElement('div');
            item.className = 'alert-item';
            if (a.risk_level === 'CRITICAL') item.classList.add('critical');
            else if (a.risk_level === 'WARNING') item.classList.add('warning');

            const hdr = document.createElement('div');
            hdr.className = 'd-flex justify-content-between';
            const lvl = document.createElement('strong');
            lvl.className = riskClass(a.risk_level);
            lvl.textContent = a.risk_level || 'ALERT';
            const tm = document.createElement('span');
            tm.className = 'alert-time';
            tm.textContent = fmtTime(a.timestamp);
            hdr.appendChild(lvl);
            hdr.appendChild(tm);

            const body = document.createElement('div');
            body.className = 'small text-secondary';
            body.textContent = (a.camera_id || '') + ' - ' + (a.message || '');

            item.appendChild(hdr);
            item.appendChild(body);
            feed.appendChild(item);
        });
    } catch { /* ignore */ }
}

function setupDashSocket() {
    if (!CS.socket) return;
    CS.socket.on('metrics_update', () => { loadStats(); loadCameraGrid(); });
    CS.socket.on('new_alert', () => { loadAlertFeed(); });
}

function setText(id, text) { const el = document.getElementById(id); if (el) el.textContent = text; }
function fmtTime(ts) {
    if (!ts) return '-';
    const d = new Date(ts);
    return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
}

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
    setupDashSocket();
    setInterval(loadStats, 5000);
});
