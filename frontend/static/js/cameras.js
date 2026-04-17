/* CrowdSafe - Camera Management */

let addModal = null;

async function loadCameras() {
    const tbody = document.getElementById('camerasBody');
    if (!tbody) return;

    try {
        const res = await apiFetch('/api/cameras');
        const cameras = await res.json();

        while (tbody.firstChild) tbody.removeChild(tbody.firstChild);

        if (cameras.length === 0) {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = 7;
            td.className = 'text-center text-secondary';
            td.textContent = 'No cameras configured. Click "Add Camera" to start.';
            tr.appendChild(td);
            tbody.appendChild(tr);
            return;
        }

        cameras.forEach(cam => {
            const tr = document.createElement('tr');

            // Name
            const tdName = document.createElement('td');
            tdName.textContent = cam.name || cam.id;
            tr.appendChild(tdName);

            // Location
            const tdLoc = document.createElement('td');
            tdLoc.textContent = cam.location || '-';
            tr.appendChild(tdLoc);

            // Area
            const tdArea = document.createElement('td');
            tdArea.textContent = String(cam.area_sqm || '-');
            tr.appendChild(tdArea);

            // Capacity
            const tdCap = document.createElement('td');
            tdCap.textContent = String(cam.expected_capacity || '-');
            tr.appendChild(tdCap);

            // Source
            const tdSrc = document.createElement('td');
            tdSrc.className = 'text-truncate';
            tdSrc.style.maxWidth = '200px';
            tdSrc.textContent = cam.source_url ? cam.source_url.split(/[\\/]/).pop() : 'None';
            tr.appendChild(tdSrc);

            // Status
            const tdStatus = document.createElement('td');
            const badge = document.createElement('span');
            if (cam.is_processing) {
                badge.className = 'badge bg-processing';
                badge.textContent = 'Processing';
            } else if (cam.source_url) {
                badge.className = 'badge bg-secondary';
                badge.textContent = 'Ready';
            } else {
                badge.className = 'badge bg-offline';
                badge.textContent = 'No Source';
            }
            tdStatus.appendChild(badge);
            tr.appendChild(tdStatus);

            // Actions
            const tdAct = document.createElement('td');
            tdAct.appendChild(makeActionButtons(cam));
            tr.appendChild(tdAct);

            tbody.appendChild(tr);
        });
    } catch {
        while (tbody.firstChild) tbody.removeChild(tbody.firstChild);
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = 7;
        td.className = 'text-center text-danger';
        td.textContent = 'Failed to load cameras';
        tr.appendChild(td);
        tbody.appendChild(tr);
    }
}

function makeActionButtons(cam) {
    const wrap = document.createElement('div');
    wrap.className = 'btn-group btn-group-sm';

    if (cam.is_processing) {
        const stopBtn = document.createElement('button');
        stopBtn.className = 'btn btn-outline-danger';
        stopBtn.textContent = 'Stop';
        stopBtn.addEventListener('click', () => stopCam(cam.id));
        wrap.appendChild(stopBtn);

        const viewBtn = document.createElement('button');
        viewBtn.className = 'btn btn-outline-info';
        viewBtn.textContent = 'View';
        viewBtn.addEventListener('click', () => { window.location.href = '/camera/' + cam.id; });
        wrap.appendChild(viewBtn);
    } else {
        if (cam.source_url) {
            const startBtn = document.createElement('button');
            startBtn.className = 'btn btn-outline-success';
            startBtn.textContent = 'Start';
            startBtn.addEventListener('click', () => startCam(cam.id));
            wrap.appendChild(startBtn);
        }
        const delBtn = document.createElement('button');
        delBtn.className = 'btn btn-outline-danger';
        delBtn.textContent = 'Delete';
        delBtn.addEventListener('click', () => deleteCam(cam.id, cam.name));
        wrap.appendChild(delBtn);
    }

    return wrap;
}

async function startCam(id) {
    try {
        const res = await apiFetch('/api/cameras/' + id + '/start', { method: 'POST' });
        const data = await res.json();
        if (!res.ok) {
            alert(data.error || 'Failed to start');
            return;
        }
        loadCameras();
    } catch { alert('Network error'); }
}

async function stopCam(id) {
    try {
        await apiFetch('/api/cameras/' + id + '/stop', { method: 'POST' });
        loadCameras();
    } catch { alert('Network error'); }
}

async function deleteCam(id, name) {
    if (!confirm('Delete camera "' + (name || id) + '"? This cannot be undone.')) return;
    try {
        await apiFetch('/api/cameras/' + id, { method: 'DELETE' });
        loadCameras();
    } catch { alert('Network error'); }
}

function showAddModal() {
    document.getElementById('addCameraForm').reset();
    const progress = document.getElementById('uploadProgress');
    if (progress) progress.classList.add('d-none');
    if (!addModal) {
        addModal = new bootstrap.Modal(document.getElementById('addModal'));
    }
    addModal.show();
}

async function handleAddCamera(e) {
    e.preventDefault();
    const btn = document.getElementById('btnSubmit');
    btn.disabled = true;
    btn.textContent = 'Creating...';

    try {
        // Step 1: Create camera
        const res = await apiFetch('/api/cameras', {
            method: 'POST',
            body: JSON.stringify({
                name: document.getElementById('camName').value,
                location: document.getElementById('camLocation').value,
                area_sqm: parseFloat(document.getElementById('camArea').value) || 100,
                expected_capacity: parseInt(document.getElementById('camCapacity').value) || 500,
            }),
        });
        const cam = await res.json();
        if (!res.ok) {
            alert(cam.error || 'Failed to create camera');
            return;
        }

        // Step 2: Upload video if provided
        const fileInput = document.getElementById('camVideo');
        if (fileInput.files.length > 0) {
            btn.textContent = 'Uploading...';
            const progress = document.getElementById('uploadProgress');
            const bar = document.getElementById('progressBar');
            if (progress) progress.classList.remove('d-none');

            const formData = new FormData();
            formData.append('video', fileInput.files[0]);

            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/cameras/' + cam.id + '/upload');
            if (CS.token) xhr.setRequestHeader('Authorization', 'Bearer ' + CS.token);

            xhr.upload.addEventListener('progress', (ev) => {
                if (ev.lengthComputable && bar) {
                    const pct = Math.round((ev.loaded / ev.total) * 100);
                    bar.style.width = pct + '%';
                }
            });

            await new Promise((resolve, reject) => {
                xhr.onload = () => {
                    if (xhr.status >= 200 && xhr.status < 300) resolve();
                    else reject(new Error('Upload failed'));
                };
                xhr.onerror = () => reject(new Error('Upload failed'));
                xhr.send(formData);
            });
        }

        if (addModal) addModal.hide();
        loadCameras();
    } catch (err) {
        alert(err.message || 'Error creating camera');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Add Camera';
    }
}

/* ---------- Init ---------- */
document.addEventListener('DOMContentLoaded', loadCameras);
