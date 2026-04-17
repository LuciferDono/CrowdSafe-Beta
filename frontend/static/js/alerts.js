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
    const tbody = document.getElementById('alertsBody');
    if (!tbody) return;

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

        while (tbody.firstChild) tbody.removeChild(tbody.firstChild);

        if (alerts.length === 0) {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = 7;
            td.className = 'text-center text-secondary py-4';
            td.textContent = 'No alerts found';
            tr.appendChild(td);
            tbody.appendChild(tr);
            return;
        }

        alerts.forEach(a => {
            const tr = document.createElement('tr');

            const tdTime = document.createElement('td');
            tdTime.className = 'text-secondary small';
            tdTime.textContent = a.timestamp ? toIST(a.timestamp) : '-';
            tr.appendChild(tdTime);

            const tdCam = document.createElement('td');
            tdCam.textContent = getCameraLabel(a.camera_id);
            tr.appendChild(tdCam);

            const tdLevel = document.createElement('td');
            const badge = document.createElement('span');
            badge.className = 'badge';
            if (a.risk_level === 'CRITICAL') badge.classList.add('bg-danger');
            else if (a.risk_level === 'WARNING') badge.classList.add('bg-warning', 'text-dark');
            else badge.classList.add('bg-secondary');
            badge.textContent = a.risk_level || '-';
            tdLevel.appendChild(badge);
            tr.appendChild(tdLevel);

            const tdMsg = document.createElement('td');
            tdMsg.textContent = a.message || '-';
            tr.appendChild(tdMsg);

            const tdRisk = document.createElement('td');
            tdRisk.textContent = a.risk_score ? (a.risk_score * 100).toFixed(0) + '%' : '-';
            tr.appendChild(tdRisk);

            const tdStatus = document.createElement('td');
            if (a.resolved) {
                tdStatus.textContent = 'Resolved';
                tdStatus.className = 'text-secondary';
            } else if (a.acknowledged) {
                tdStatus.textContent = 'Acknowledged';
                tdStatus.className = 'text-warning';
            } else {
                tdStatus.textContent = 'Open';
                tdStatus.className = 'text-danger';
            }
            tr.appendChild(tdStatus);

            const tdAct = document.createElement('td');
            tdAct.className = 'text-end';
            if (!a.acknowledged) {
                const ackBtn = document.createElement('button');
                ackBtn.className = 'btn btn-outline-warning btn-sm me-1';
                ackBtn.textContent = 'Ack';
                ackBtn.addEventListener('click', () => ackAlert(a.alert_id || a.id));
                tdAct.appendChild(ackBtn);
            }
            if (!a.resolved) {
                const resBtn = document.createElement('button');
                resBtn.className = 'btn btn-outline-success btn-sm';
                resBtn.textContent = 'Resolve';
                resBtn.addEventListener('click', () => resolveAlert(a.alert_id || a.id));
                tdAct.appendChild(resBtn);
            }
            tr.appendChild(tdAct);

            tbody.appendChild(tr);
        });
    } catch {
        while (tbody.firstChild) tbody.removeChild(tbody.firstChild);
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = 7;
        td.className = 'text-center text-danger py-4';
        td.textContent = 'Failed to load alerts';
        tr.appendChild(td);
        tbody.appendChild(tr);
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
