/* CrowdSafe — Dashboard orchestration */

const Dash = {
    heatmapCtx: null,
    heatmapCamId: null,
    lastPeople: 0,
    uptimeSeconds: 0,
};

/* ---------- Stats ---------- */
async function loadStats() {
    try {
        const res = await apiFetch('/api/metrics/summary');
        const d = await res.json();
        const total = Number(d.total_people || 0);
        setText('totalPeople', formatNumber(total));

        const trend = document.getElementById('peopleTrend');
        if (trend) {
            const delta = total - Dash.lastPeople;
            trend.className = 'stat-trend ' + (delta > 0 ? 'up' : (delta < 0 ? 'down' : 'text-dim'));
            trend.textContent = delta === 0
                ? 'steady'
                : (delta > 0 ? '▲ +' : '▼ ') + Math.abs(delta) + ' vs last tick';
        }
        Dash.lastPeople = total;

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
        setText('statMetrics', formatNumber(d3.metrics_recorded || 0));
        setText('totalCameras', String(d3.cameras_total || 0));
    } catch { /* ignore */ }

    try {
        const res4 = await apiFetch('/api/system/health');
        const d4 = await res4.json();
        Dash.uptimeSeconds = d4.uptime_seconds || 0;
        setText('statUptime', formatUptime(Dash.uptimeSeconds));
    } catch { /* ignore */ }
}

function formatNumber(n) {
    if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
    return String(n);
}

function formatUptime(s) {
    if (s < 60) return s + 's';
    if (s < 3600) return Math.floor(s / 60) + 'm';
    if (s < 86400) return Math.floor(s / 3600) + 'h';
    return Math.floor(s / 86400) + 'd';
}

/* ---------- Camera grid ---------- */
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
            // Clear any prior tiles
            grid.querySelectorAll('.cam-tile-wrap').forEach(t => t.remove());
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
                wrap.className = 'col-md-6 col-xl-6 cam-tile-wrap';
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
                name.className = 'camera-tile-name';
                name.textContent = cam.name || cam.id;
                const meta = document.createElement('span');
                meta.className = 'tile-meta';
                info.appendChild(name);
                info.appendChild(meta);

                tile.appendChild(img);
                tile.appendChild(info);
                wrap.appendChild(tile);
                grid.appendChild(wrap);
            }
            const meta = wrap.querySelector('.tile-meta');
            if (meta) renderCamMeta(meta, cam);
        });

        // Pick first active cam for heatmap + forecast by default.
        if (!Dash.heatmapCamId && active.length > 0) {
            Dash.heatmapCamId = active[0].id;
            setText('heatmapCamName', active[0].name || active[0].id);
            loadHeatmap(active[0].id);
            loadForecast(active[0].id);
        }
    } catch { /* ignore */ }
}

function renderCamMeta(el, cam) {
    while (el.firstChild) el.removeChild(el.firstChild);
    const m = cam.current_metrics || {};
    const chip = document.createElement('span');
    const level = (m.risk_level || 'SAFE').toLowerCase();
    chip.className = 'risk-chip ' + level;
    chip.textContent = m.risk_level || 'SAFE';
    const count = document.createElement('span');
    count.className = 'text-dim';
    count.textContent = (m.count || 0) + ' ppl';
    el.appendChild(count);
    el.appendChild(chip);
}

/* ---------- Alert feed ---------- */
async function loadAlertFeed() {
    const feed = document.getElementById('alertFeed');
    if (!feed) return;
    try {
        const res = await apiFetch('/api/alerts?limit=10');
        const alerts = await res.json();
        while (feed.firstChild) feed.removeChild(feed.firstChild);

        if (!alerts || alerts.length === 0) {
            const p = document.createElement('p');
            p.className = 'text-mute small text-center mb-0 py-4';
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
            hdr.className = 'd-flex justify-content-between align-items-center mb-1';
            const lvl = document.createElement('strong');
            lvl.className = riskClass(a.risk_level);
            lvl.textContent = a.risk_level || 'ALERT';
            const tm = document.createElement('span');
            tm.className = 'alert-time';
            tm.textContent = fmtTime(a.timestamp);
            hdr.appendChild(lvl);
            hdr.appendChild(tm);

            const body = document.createElement('div');
            body.className = 'small text-dim';
            body.textContent = (a.camera_id || '') + ' — ' + (a.message || '');

            item.appendChild(hdr);
            item.appendChild(body);
            feed.appendChild(item);
        });
    } catch { /* ignore */ }
}

/* ---------- Heatmap rendering ---------- */
async function loadHeatmap(camId) {
    const canvas = document.getElementById('heatmapCanvas');
    if (!canvas || !camId) return;
    const ctx = canvas.getContext('2d');

    try {
        const res = await apiFetch('/api/cameras/' + encodeURIComponent(camId) + '/heatmap/current');
        if (!res.ok) {
            drawHeatmapPlaceholder(ctx, canvas, 'No heatmap data yet');
            return;
        }
        const payload = await res.json();
        if (!payload.grid_data) {
            drawHeatmapPlaceholder(ctx, canvas, 'Awaiting sample');
            return;
        }
        renderHeatmap(ctx, canvas, payload);
        const meta = document.getElementById('heatmapMeta');
        if (meta) {
            meta.textContent = payload.person_count + ' people · ' +
                payload.grid_rows + '×' + payload.grid_cols + ' grid · ' +
                new Date(payload.timestamp).toLocaleTimeString();
        }
    } catch {
        drawHeatmapPlaceholder(ctx, canvas, 'Heatmap error');
    }
}

function drawHeatmapPlaceholder(ctx, canvas, text) {
    ctx.fillStyle = '#07090f';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#64748b';
    ctx.font = '13px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, canvas.width / 2, canvas.height / 2);
}

function renderHeatmap(ctx, canvas, payload) {
    const rows = payload.grid_rows;
    const cols = payload.grid_cols;
    // Decode base64 → uint8 → normalized [0,1]
    const raw = atob(payload.grid_data);
    const bytes = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);

    // Fit canvas cells
    canvas.width = canvas.clientWidth || 320;
    canvas.height = canvas.clientHeight || Math.round((canvas.width / 16) * 9);
    const cellW = canvas.width / cols;
    const cellH = canvas.height / rows;

    ctx.fillStyle = '#07090f';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            const v = bytes[r * cols + c] / 255;
            ctx.fillStyle = heatColor(v);
            ctx.fillRect(c * cellW, r * cellH, Math.ceil(cellW) + 1, Math.ceil(cellH) + 1);
        }
    }
}

// Blue → cyan → yellow → orange → red gradient
function heatColor(t) {
    if (t <= 0) return 'rgba(7,9,15,0)';
    const stops = [
        [0.00, [12, 74, 110]],
        [0.25, [6, 182, 212]],
        [0.50, [234, 179, 8]],
        [0.75, [249, 115, 22]],
        [1.00, [239, 68, 68]],
    ];
    for (let i = 1; i < stops.length; i++) {
        if (t <= stops[i][0]) {
            const [a, b] = [stops[i - 1], stops[i]];
            const f = (t - a[0]) / (b[0] - a[0] || 1);
            const r = Math.round(a[1][0] + (b[1][0] - a[1][0]) * f);
            const g = Math.round(a[1][1] + (b[1][1] - a[1][1]) * f);
            const bl = Math.round(a[1][2] + (b[1][2] - a[1][2]) * f);
            return 'rgba(' + r + ',' + g + ',' + bl + ',' + (0.25 + 0.6 * t).toFixed(2) + ')';
        }
    }
    return 'rgb(239,68,68)';
}

/* ---------- Forecast cards ---------- */
async function loadForecast(camId) {
    if (!camId) return;
    try {
        const [fRes, pRes] = await Promise.all([
            apiFetch('/api/forecast/' + encodeURIComponent(camId)),
            apiFetch('/api/cameras/' + encodeURIComponent(camId) + '/popular-times'),
        ]);
        const fData = fRes.ok ? await fRes.json() : null;
        const pData = pRes.ok ? await pRes.json() : null;
        if (fData) renderForecast(fData, pData);
    } catch { /* ignore */ }
}

function _forecastPoint(points, targetSec) {
    return points.find(p => Math.abs((p.t_plus_sec || p.offset_seconds || 0) - targetSec) <= 8)
        || points[points.length - 1];
}

function _riskColor(level) {
    const map = { SAFE: 'var(--ok)', CAUTION: 'var(--caution)', WARNING: 'var(--warn)', CRITICAL: 'var(--danger)' };
    return map[(level || 'SAFE').toUpperCase()] || 'var(--text-dim)';
}

function _makeCard(label, point) {
    const card = document.createElement('div');
    card.className = 'forecast-card';

    const lbl = document.createElement('div');
    lbl.className = 'fc-label';
    lbl.textContent = label;

    const cnt = document.createElement('div');
    cnt.className = 'fc-count';
    const count = point
        ? Math.round(point.predicted_count != null ? point.predicted_count : (point.count ?? 0))
        : '—';
    cnt.textContent = count;

    const unit = document.createElement('div');
    unit.className = 'fc-unit';
    unit.textContent = 'people';

    const risk = document.createElement('div');
    risk.className = 'fc-risk';
    const lvl = point ? (point.risk_level || point.level || 'SAFE') : 'SAFE';
    risk.textContent = lvl;
    risk.style.color = _riskColor(lvl);

    card.appendChild(lbl);
    card.appendChild(cnt);
    card.appendChild(unit);
    card.appendChild(risk);
    return card;
}

function renderForecast(data, popularData) {
    const wrap = document.getElementById('forecastWrap');
    if (!wrap) return;

    while (wrap.firstChild) wrap.removeChild(wrap.firstChild);

    const points = data.forecast || data.predictions || data.points || [];
    if (!points.length) {
        const empty = document.createElement('div');
        empty.style.cssText = 'color:var(--text-mute);font-size:0.8rem;padding:20px 0;text-align:center';
        empty.textContent = 'No forecast data';
        wrap.appendChild(empty);
        return;
    }

    /* --- milestone cards: Now / +2 min / +5 min --- */
    const nowPt = points[0];
    const pt2 = _forecastPoint(points, 120);
    const pt5 = _forecastPoint(points, 300);

    const cards = document.createElement('div');
    cards.className = 'forecast-cards';
    cards.appendChild(_makeCard('Now', nowPt));
    cards.appendChild(_makeCard('+2 min', pt2));
    cards.appendChild(_makeCard('+5 min', pt5));
    wrap.appendChild(cards);

    /* --- risk timeline bar --- */
    const tlWrap = document.createElement('div');
    tlWrap.className = 'forecast-timeline';
    const step = Math.max(1, Math.floor(points.length / 12));
    for (let i = 0; i < points.length; i += step) {
        const seg = document.createElement('div');
        const lvl = (points[i].risk_level || points[i].level || 'SAFE').toUpperCase();
        const cls = { SAFE: 'ft-safe', CAUTION: 'ft-caution', WARNING: 'ft-warning', CRITICAL: 'ft-critical' }[lvl] || 'ft-safe';
        seg.className = cls;
        seg.style.flex = '1';
        tlWrap.appendChild(seg);
    }
    wrap.appendChild(tlWrap);

    /* --- axis labels: Now ... +5min --- */
    const axis = document.createElement('div');
    axis.style.cssText = 'display:flex;justify-content:space-between;font-size:0.62rem;color:var(--text-mute);margin-top:2px';
    const axNow = document.createElement('span');
    axNow.textContent = 'Now';
    const axEnd = document.createElement('span');
    axEnd.textContent = '+5 min';
    axis.appendChild(axNow);
    axis.appendChild(axEnd);
    wrap.appendChild(axis);

    /* --- insight + historical comparison --- */
    const insight = document.createElement('div');
    insight.className = 'forecast-insight';

    const maxPt = points.reduce((a, b) =>
        (a.predicted_count || a.count || 0) > (b.predicted_count || b.count || 0) ? a : b, points[0]);
    const maxCount = Math.round(maxPt.predicted_count != null ? maxPt.predicted_count : (maxPt.count || 0));
    const maxSec = maxPt.t_plus_sec || maxPt.offset_seconds || 0;
    const peakLabel = maxSec === 0 ? 'now' : '+' + Math.round(maxSec / 60) + ' min';

    let insightText = 'Peak of ' + maxCount + ' people expected ' + peakLabel + '.';

    if (popularData && popularData.peak_hour != null) {
        const ph = popularData.peak_hour;
        const ampm = ph >= 12 ? 'PM' : 'AM';
        const h12 = ph > 12 ? ph - 12 : (ph === 0 ? 12 : ph);
        insightText += ' Historically busiest at ' + h12 + ampm + '.';
    }

    insight.textContent = insightText;
    wrap.appendChild(insight);
}

/* ---------- NL search ---------- */
async function runNlSearch() {
    const input = document.getElementById('nlSearchInput');
    const btn = document.getElementById('nlSearchBtn');
    const resultsEl = document.getElementById('nlResults');
    if (!input || !resultsEl) return;
    const q = input.value.trim();
    if (!q) return;

    btn.disabled = true;
    btn.textContent = 'Searching…';
    resultsEl.classList.remove('d-none');
    while (resultsEl.firstChild) resultsEl.removeChild(resultsEl.firstChild);
    const loading = document.createElement('div');
    loading.className = 'nl-results-header';
    loading.textContent = 'Running NL search…';
    resultsEl.appendChild(loading);

    try {
        const res = await apiFetch('/api/search/nl', {
            method: 'POST',
            body: JSON.stringify({ q }),
        });
        const data = await res.json();
        renderNlResults(resultsEl, data, res.ok);
    } catch (e) {
        while (resultsEl.firstChild) resultsEl.removeChild(resultsEl.firstChild);
        const err = document.createElement('div');
        err.className = 'nl-results-header risk-critical';
        err.textContent = 'Error: ' + e.message;
        resultsEl.appendChild(err);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Search';
    }
}

function renderNlResults(root, data, ok) {
    while (root.firstChild) root.removeChild(root.firstChild);

    if (!ok || data.error) {
        const err = document.createElement('div');
        err.className = 'nl-results-header risk-critical';
        err.textContent = data.error || 'Search failed';
        root.appendChild(err);
        return;
    }

    const header = document.createElement('div');
    header.className = 'nl-results-header';
    const left = document.createElement('span');
    left.textContent = data.count + ' result(s) in ' + (data.spec ? data.spec.table : '?');
    const right = document.createElement('span');
    right.className = 'text-mute';
    right.textContent = JSON.stringify((data.spec && data.spec.filters) || {});
    header.appendChild(left);
    header.appendChild(right);
    root.appendChild(header);

    (data.results || []).slice(0, 50).forEach(r => {
        const row = document.createElement('div');
        row.className = 'nl-row';

        const badge = document.createElement('span');
        badge.className = 'risk-chip ' + (r.risk_level || 'safe').toLowerCase();
        badge.textContent = r.risk_level || '—';

        const mid = document.createElement('span');
        mid.className = 'text-dim';
        const parts = [];
        if (r.camera_id) parts.push(r.camera_id);
        if (r.count != null) parts.push(r.count + ' ppl');
        if (r.density != null) parts.push('d=' + Number(r.density).toFixed(2));
        if (r.trigger_condition) parts.push(r.trigger_condition);
        if (r.message) parts.push(r.message);
        mid.textContent = parts.join(' · ');

        const time = document.createElement('span');
        time.className = 'alert-time';
        time.textContent = fmtTime(r.timestamp);

        row.appendChild(badge);
        row.appendChild(mid);
        row.appendChild(time);
        root.appendChild(row);
    });
}

/* ---------- Socket wiring ---------- */
function setupDashSocket() {
    if (!CS.socket) return;
    CS.socket.on('metrics_update', () => { loadStats(); loadCameraGrid(); });
    CS.socket.on('new_alert', () => { loadAlertFeed(); });
}

/* ---------- Helpers ---------- */
function setText(id, text) { const el = document.getElementById(id); if (el) el.textContent = text; }
function fmtTime(ts) {
    if (!ts) return '-';
    const d = new Date(ts);
    return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
}

/* ---------- Bootstrap ---------- */
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadCameraGrid();
    loadAlertFeed();
    setupDashSocket();

    const form = document.getElementById('nlSearchForm');
    if (form) form.addEventListener('submit', (e) => { e.preventDefault(); runNlSearch(); });

    setInterval(loadStats, 5000);
    setInterval(loadCameraGrid, 10000);
    setInterval(() => Dash.heatmapCamId && loadHeatmap(Dash.heatmapCamId), 15000);
    setInterval(() => Dash.heatmapCamId && loadForecast(Dash.heatmapCamId), 30000);
});
