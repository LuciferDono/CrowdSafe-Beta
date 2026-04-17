/* CrowdSafe - Settings */

async function loadSettings() {
    try {
        const res = await apiFetch('/api/settings');
        const data = await res.json();

        // Risk thresholds
        const risk = data.risk || {};
        setVal('setDensityWarn', risk.density_warning || '2.0');
        setVal('setDensityCrit', risk.density_critical || '4.0');
        setVal('setVelStagnant', risk.velocity_stagnant || '0.2');
        setVal('setWD', risk.weight_density || '0.5');
        setVal('setWS', risk.weight_surge || '0.3');
        setVal('setWV', risk.weight_velocity || '0.2');

        // Alert settings
        const alertCfg = data.alerts || data.alert || {};
        setVal('setCooldown', alertCfg.cooldown_seconds || '60');
        setChecked('setEmailEnabled', alertCfg.email_enabled === 'true');
        setChecked('setSmsEnabled', alertCfg.sms_enabled === 'true');
        setChecked('setTelegramEnabled', alertCfg.telegram_enabled === 'true');
        setVal('setTelegramToken', alertCfg.telegram_bot_token || '');
        setVal('setTelegramChatId', alertCfg.telegram_chat_id || '');

        // AI settings
        const ai = data.ai || {};
        setVal('setModel', ai.model || 'yolo11n.pt');
        setVal('setConf', ai.confidence_threshold || '0.35');
        setVal('setIou', ai.iou_threshold || '0.45');
    } catch { /* ignore */ }
}

async function saveRiskSettings() {
    const payload = {
        density_warning: getVal('setDensityWarn'),
        density_critical: getVal('setDensityCrit'),
        velocity_stagnant: getVal('setVelStagnant'),
        weight_density: getVal('setWD'),
        weight_surge: getVal('setWS'),
        weight_velocity: getVal('setWV'),
    };
    try {
        const res = await apiFetch('/api/settings/risk-thresholds', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        if (res.ok) showToast('Settings', 'Risk settings saved');
        else showToast('Error', 'Failed to save risk settings');
    } catch { showToast('Error', 'Network error'); }
}

async function saveAlertSettings() {
    const items = {
        cooldown_seconds: getVal('setCooldown'),
        email_enabled: getChecked('setEmailEnabled') ? 'true' : 'false',
        sms_enabled: getChecked('setSmsEnabled') ? 'true' : 'false',
        telegram_enabled: getChecked('setTelegramEnabled') ? 'true' : 'false',
        telegram_bot_token: getVal('setTelegramToken'),
        telegram_chat_id: getVal('setTelegramChatId'),
    };
    try {
        for (const [key, value] of Object.entries(items)) {
            await apiFetch('/api/settings/alerts/' + key, {
                method: 'PUT',
                body: JSON.stringify({ value: value }),
            });
        }
        showToast('Settings', 'Alert settings saved successfully');
    } catch {
        showToast('Error', 'Failed to save alert settings');
    }
}

async function saveAiSettings() {
    const items = {
        confidence_threshold: getVal('setConf'),
        iou_threshold: getVal('setIou'),
    };
    try {
        for (const [key, value] of Object.entries(items)) {
            await apiFetch('/api/settings/ai/' + key, {
                method: 'PUT',
                body: JSON.stringify({ value: value }),
            });
        }
        showToast('Settings', 'AI settings saved');
    } catch { showToast('Error', 'Network error'); }
}

function getVal(id) {
    const el = document.getElementById(id);
    return el ? el.value : '';
}

function setVal(id, val) {
    const el = document.getElementById(id);
    if (el) el.value = val;
}

function getChecked(id) {
    const el = document.getElementById(id);
    return el ? el.checked : false;
}

function setChecked(id, val) {
    const el = document.getElementById(id);
    if (el) el.checked = val;
}

/* ---------- Init ---------- */
document.addEventListener('DOMContentLoaded', loadSettings);
