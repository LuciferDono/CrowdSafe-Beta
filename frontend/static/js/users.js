/* CrowdSafe - User Management */

let addUserModal = null;

async function loadUsers() {
    const tbody = document.getElementById('usersBody');
    if (!tbody) return;

    try {
        const res = await apiFetch('/api/users');
        const users = await res.json();

        while (tbody.firstChild) tbody.removeChild(tbody.firstChild);

        if (users.length === 0) {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = 7;
            td.className = 'text-center text-secondary';
            td.textContent = 'No users found';
            tr.appendChild(td);
            tbody.appendChild(tr);
            return;
        }

        users.forEach(u => {
            const tr = document.createElement('tr');

            // Username
            const tdUser = document.createElement('td');
            tdUser.textContent = u.username;
            tr.appendChild(tdUser);

            // Full Name
            const tdName = document.createElement('td');
            tdName.textContent = u.full_name || '-';
            tr.appendChild(tdName);

            // Email
            const tdEmail = document.createElement('td');
            tdEmail.textContent = u.email;
            tr.appendChild(tdEmail);

            // Role
            const tdRole = document.createElement('td');
            const roleBadge = document.createElement('span');
            roleBadge.className = 'badge';
            if (u.role === 'admin') roleBadge.classList.add('bg-danger');
            else if (u.role === 'operator') roleBadge.classList.add('bg-warning', 'text-dark');
            else roleBadge.classList.add('bg-secondary');
            roleBadge.textContent = u.role;
            tdRole.appendChild(roleBadge);
            tr.appendChild(tdRole);

            // Active
            const tdActive = document.createElement('td');
            const dot = document.createElement('span');
            dot.className = 'status-dot ' + (u.is_active ? 'active' : 'inactive');
            tdActive.appendChild(dot);
            const activeText = document.createTextNode(u.is_active ? 'Yes' : 'No');
            tdActive.appendChild(activeText);
            tr.appendChild(tdActive);

            // Last Login
            const tdLogin = document.createElement('td');
            tdLogin.className = 'text-secondary small';
            tdLogin.textContent = u.last_login ? new Date(u.last_login).toLocaleString() : 'Never';
            tr.appendChild(tdLogin);

            // Actions
            const tdAct = document.createElement('td');
            const btnGroup = document.createElement('div');
            btnGroup.className = 'btn-group btn-group-sm';

            const toggleBtn = document.createElement('button');
            toggleBtn.className = 'btn btn-outline-secondary';
            toggleBtn.textContent = u.is_active ? 'Disable' : 'Enable';
            toggleBtn.addEventListener('click', () => toggleUser(u.id, !u.is_active));
            btnGroup.appendChild(toggleBtn);

            const resetBtn = document.createElement('button');
            resetBtn.className = 'btn btn-outline-warning';
            resetBtn.textContent = 'Reset PW';
            resetBtn.addEventListener('click', () => resetPassword(u.id, u.username));
            btnGroup.appendChild(resetBtn);

            if (u.username !== 'admin') {
                const delBtn = document.createElement('button');
                delBtn.className = 'btn btn-outline-danger';
                delBtn.textContent = 'Delete';
                delBtn.addEventListener('click', () => deleteUser(u.id, u.username));
                btnGroup.appendChild(delBtn);
            }

            tdAct.appendChild(btnGroup);
            tr.appendChild(tdAct);

            tbody.appendChild(tr);
        });
    } catch {
        while (tbody.firstChild) tbody.removeChild(tbody.firstChild);
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = 7;
        td.className = 'text-center text-danger';
        td.textContent = 'Failed to load users';
        tr.appendChild(td);
        tbody.appendChild(tr);
    }
}

async function toggleUser(id, active) {
    try {
        await apiFetch('/api/users/' + id, {
            method: 'PUT',
            body: JSON.stringify({ is_active: active }),
        });
        loadUsers();
    } catch { alert('Network error'); }
}

async function resetPassword(id, username) {
    if (!confirm('Reset password for "' + username + '"?')) return;
    try {
        const res = await apiFetch('/api/users/' + id + '/reset-password', { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
            alert('Temporary password: ' + data.temporary_password);
        } else {
            alert(data.error || 'Failed');
        }
    } catch { alert('Network error'); }
}

async function deleteUser(id, username) {
    if (!confirm('Delete user "' + username + '"? This cannot be undone.')) return;
    try {
        await apiFetch('/api/users/' + id, { method: 'DELETE' });
        loadUsers();
    } catch { alert('Network error'); }
}

function showAddUserModal() {
    document.getElementById('addUserForm').reset();
    if (!addUserModal) {
        addUserModal = new bootstrap.Modal(document.getElementById('addUserModal'));
    }
    addUserModal.show();
}

async function handleAddUser(e) {
    e.preventDefault();
    try {
        const res = await apiFetch('/api/users', {
            method: 'POST',
            body: JSON.stringify({
                username: document.getElementById('newUsername').value,
                full_name: document.getElementById('newFullName').value,
                email: document.getElementById('newEmail').value,
                password: document.getElementById('newPassword').value,
                role: document.getElementById('newRole').value,
            }),
        });
        const data = await res.json();
        if (!res.ok) {
            alert(data.error || 'Failed to create user');
            return;
        }
        if (addUserModal) addUserModal.hide();
        loadUsers();
    } catch { alert('Network error'); }
}

/* ---------- Init ---------- */
document.addEventListener('DOMContentLoaded', loadUsers);
