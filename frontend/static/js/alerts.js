/* CrowdSafe - Alerts Page */

let _cameraCache = {};

async function loadCameraNames() {
    try {
        const res = await apiFetch('/api/cameras');
        const cameras = await res.json();
        cameras.forEach(c => { _cameraCache[c.id] = c; });
    } catch { /* ignore */ }
}

function getCameraLabel(camId) {
    const cam = _cameraCache[camId];
    if (!cam) return camId || '-';
    let label = cam.name || camId;
    if (cam.location) label += ' (' + cam.location + ')';
    return label;
}

async function loadAlerts() {
    const grid = document.getElementById('alertsGrid');
    if (!grid) return;

    if (Object.keys(_cameraCache).length === 0) await loadCameraNames();

    const level = document.getElementById('filterLevel').value;
    const resolved = document.getElementById('filterResolved').value;
    let url = '/api/alerts?limit=100';
    if (level) url += '&risk_level=' + level;
    if (resolved) url += '&resolved=' + resolved;

    try {
        const res = await apiFetch(url);
        const alerts = await res.json();

        const countEl = document.getElementById('alertCount');
        if (countEl) countEl.textContent = alerts.length + ' alerts';

        while (grid.firstChild) grid.removeChild(grid.firstChild);

        if (alerts.length === 0) {
            const div = document.createElement('div');
            div.style.gridColumn = '1 / -1';
            div.className = 'text-center text-secondary py-5 w-100';
            div.textContent = 'No alerts found';
            grid.appendChild(div);
            return;
        }

        alerts.forEach(a => {
            const card = document.createElement('div');
            card.className = 'panel d-flex flex-column gap-3';
            
            // Risk specific styling
            let badgeClass = 'bg-secondary text-white';
            let borderClass = 'var(--border)';
            
            if (a.risk_level === 'CRITICAL') {
                badgeClass = 'bg-danger text-white';
                borderClass = 'var(--danger)';
            } else if (a.risk_level === 'WARNING') {
                badgeClass = 'bg-warning text-dark';
                borderClass = 'var(--warn)';
            } else if (a.risk_level === 'CAUTION') {
                badgeClass = 'bg-info text-dark';
                borderClass = 'var(--caution)';
            }
            
            card.style.borderTop = `3px solid ${borderClass}`;
            
            const timeStr = a.timestamp ? toIST(a.timestamp) : '-';
            const riskScore = a.risk_score ? (a.risk_score * 100).toFixed(0) + '%' : '-';
            
            let statusHtml = '';
            if (a.resolved) {
                statusHtml = '<span class="text-success small fw-bold"><i class="bi bi-check-circle"></i> Resolved</span>';
            } else if (a.acknowledged) {
                statusHtml = '<span class="text-warning small fw-bold"><i class="bi bi-clock"></i> Acknowledged</span>';
            } else {
                statusHtml = '<span class="text-danger small fw-bold"><i class="bi bi-exclamation-circle"></i> Open</span>';
            }
            
            let actionsHtml = '';
            if (!a.acknowledged) {
                actionsHtml += `<button class="btn btn-outline-warning btn-sm" onclick="ackAlert('${a.alert_id || a.id}')">Acknowledge</button>`;
            }
            if (!a.resolved) {
                actionsHtml += `<button class="btn btn-outline-success btn-sm" onclick="resolveAlert('${a.alert_id || a.id}')">Resolve</button>`;
            }
            
            card.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <span class="badge ${badgeClass} fs-6">${a.risk_level || '-'}</span>
                    <span class="text-secondary small"><i class="bi bi-clock me-1"></i>${timeStr}</span>
                </div>
                <div>
                    <h6 class="text-white mb-2" style="font-size: 0.95rem;">
                        <i class="bi bi-camera-video me-2 text-muted"></i>${getCameraLabel(a.camera_id)}
                    </h6>
                    <p class="text-light small mb-0" style="opacity: 0.85; line-height: 1.5;">${a.message || '-'}</p>
                </div>
                <div class="mt-auto pt-3 border-top d-flex justify-content-between align-items-end" style="border-color: var(--border-strong) !important;">
                    <div>
                        <div class="text-muted" style="font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Risk Score</div>
                        <div class="text-white fw-bold" style="font-size: 1.25rem;">${riskScore}</div>
                    </div>
                    <div class="d-flex flex-column align-items-end gap-2">
                        ${statusHtml}
                        <div class="d-flex gap-2">
                            ${actionsHtml}
                        </div>
                    </div>
                </div>
            `;
            grid.appendChild(card);
        });
    } catch {
        while (grid.firstChild) grid.removeChild(grid.firstChild);
        const div = document.createElement('div');
        div.style.gridColumn = '1 / -1';
        div.className = 'text-center text-danger py-5 w-100';
        div.textContent = 'Failed to load alerts';
        grid.appendChild(div);
    }
}

async function ackAlert(id) {
    try {
        await apiFetch('/api/alerts/' + id + '/acknowledge', { method: 'POST' });
        loadAlerts();
    } catch { /* ignore */ }
}

async function resolveAlert(id) {
    try {
        await apiFetch('/api/alerts/' + id + '/resolve', { method: 'POST' });
        loadAlerts();
    } catch { /* ignore */ }
}

document.addEventListener('DOMContentLoaded', loadAlerts);
