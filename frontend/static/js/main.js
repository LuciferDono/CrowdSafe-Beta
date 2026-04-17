/* CrowdSafe - Global: SocketIO, Auth, Clock, Alerts */

const CS = {
    socket: null,
    token: localStorage.getItem('access_token'),
    user: JSON.parse(localStorage.getItem('user') || 'null'),
};

/* ---- Auth ---- */
function authHeaders() {
    const h = { 'Content-Type': 'application/json' };
    if (CS.token) h['Authorization'] = 'Bearer ' + CS.token;
    return h;
}

async function apiFetch(url, opts = {}) {
    opts.headers = Object.assign(authHeaders(), opts.headers || {});
    const res = await fetch(url, opts);
    if (res.status === 401) {
        const ok = await tryRefresh();
        if (ok) {
            opts.headers['Authorization'] = 'Bearer ' + CS.token;
            return fetch(url, opts);
        }
        window.location.href = '/login';
    }
    return res;
}

async function tryRefresh() {
    const rt = localStorage.getItem('refresh_token');
    if (!rt) return false;
    try {
        const res = await fetch('/api/auth/refresh', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: rt }),
        });
        if (!res.ok) return false;
        const data = await res.json();
        CS.token = data.access_token;
        localStorage.setItem('access_token', data.access_token);
        return true;
    } catch { return false; }
}

function doLogout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    fetch('/api/auth/logout', { method: 'POST', headers: authHeaders() })
        .finally(() => { window.location.href = '/login'; });
}

/* ---- IST Formatter ---- */
function toIST(date) {
    if (typeof date === 'string') date = new Date(date);
    return date.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' });
}

function toISTTime(date) {
    if (typeof date === 'string') date = new Date(date);
    return date.toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false });
}

function toISTDate(date) {
    if (typeof date === 'string') date = new Date(date);
    return date.toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: 'numeric' });
}

/* ---- Clock (IST) ---- */
function updateClock() {
    const el = document.getElementById('liveClock');
    if (!el) return;
    el.textContent = toISTTime(new Date()) + ' IST';
}

/* ---- WebSocket ---- */
function initSocket() {
    CS.socket = io({ transports: ['websocket', 'polling'] });
    const dot = document.getElementById('wsStatus');
    CS.socket.on('connect', () => { if (dot) dot.classList.add('connected'); });
    CS.socket.on('disconnect', () => { if (dot) dot.classList.remove('connected'); });
    CS.socket.on('new_alert', (data) => {
        showToast(data.risk_level || 'Alert', data.message || 'Risk threshold exceeded');
        updateAlertBadge();
    });
}

/* ---- Toast ---- */
function showToast(title, message) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast show align-items-center border-danger';
    toast.setAttribute('role', 'alert');

    const d = document.createElement('div');
    d.className = 'd-flex';

    const body = document.createElement('div');
    body.className = 'toast-body';
    const strong = document.createElement('strong');
    strong.textContent = title;
    const msg = document.createElement('div');
    msg.className = 'small text-secondary';
    msg.textContent = message;
    body.appendChild(strong);
    body.appendChild(msg);

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn-close me-2 m-auto';
    btn.addEventListener('click', () => toast.remove());

    d.appendChild(body);
    d.appendChild(btn);
    toast.appendChild(d);
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 8000);
}

/* ---- Alert badge ---- */
async function updateAlertBadge() {
    try {
        const res = await apiFetch('/api/alerts/unacknowledged/count');
        const data = await res.json();
        const badge = document.getElementById('sidebarAlertCount');
        if (!badge) return;
        if (data.count > 0) {
            badge.textContent = String(data.count);
            badge.classList.remove('d-none');
        } else {
            badge.classList.add('d-none');
        }
    } catch { /* ignore */ }
}

/* ---- User ---- */
function updateUserDisplay() {
    const el = document.getElementById('currentUserName');
    if (el && CS.user) el.textContent = CS.user.username || 'admin';
}

/* ---- Risk class helper ---- */
function riskClass(level) {
    const l = (level || '').toUpperCase();
    if (l === 'CRITICAL') return 'risk-critical';
    if (l === 'WARNING') return 'risk-warning';
    if (l === 'CAUTION') return 'risk-caution';
    return 'risk-safe';
}

/* ---- Init ---- */
document.addEventListener('DOMContentLoaded', () => {
    updateClock();
    setInterval(updateClock, 1000);
    initSocket();
    updateAlertBadge();
    updateUserDisplay();
    setInterval(updateAlertBadge, 30000);
});
