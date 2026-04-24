/* CrowdSafe Copilot — floating LLM assistant grounded on live state */

const Copilot = {
    panel: null,
    fab: null,
    body: null,
    input: null,
    sendBtn: null,
    status: null,
    open: false,
    history: [],
    aiReady: false,
};

function copilotOpen() {
    if (!Copilot.panel) return;
    Copilot.panel.classList.remove('d-none');
    Copilot.open = true;
    setTimeout(() => Copilot.input && Copilot.input.focus(), 80);
}

function copilotClose() {
    if (!Copilot.panel) return;
    Copilot.panel.classList.add('d-none');
    Copilot.open = false;
}

function copilotToggle() {
    if (Copilot.open) copilotClose(); else copilotOpen();
}

function copilotAppend(role, text, meta) {
    if (!Copilot.body) return;
    const msg = document.createElement('div');
    msg.className = 'copilot-msg ' + role;
    msg.textContent = text;
    if (meta) {
        const m = document.createElement('div');
        m.className = 'copilot-meta';
        m.textContent = meta;
        msg.appendChild(m);
    }
    Copilot.body.appendChild(msg);
    Copilot.body.scrollTop = Copilot.body.scrollHeight;
    return msg;
}

function copilotTyping() {
    const wrap = document.createElement('div');
    wrap.className = 'copilot-msg assistant';
    const dots = document.createElement('div');
    dots.className = 'typing-dots';
    for (let i = 0; i < 3; i++) dots.appendChild(document.createElement('span'));
    wrap.appendChild(dots);
    Copilot.body.appendChild(wrap);
    Copilot.body.scrollTop = Copilot.body.scrollHeight;
    return wrap;
}

async function copilotAsk(question) {
    if (!question || !question.trim()) return;
    if (!Copilot.aiReady) {
        copilotAppend('system', 'AI is offline. Set OR_API_KEY in .env to enable.');
        return;
    }

    copilotAppend('user', question);
    Copilot.input.value = '';
    Copilot.sendBtn.disabled = true;
    const typing = copilotTyping();

    try {
        const res = await apiFetch('/api/copilot/chat', {
            method: 'POST',
            body: JSON.stringify({ message: question, include_live: true }),
        });
        typing.remove();

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            copilotAppend('system', err.error || ('Request failed: ' + res.status));
        } else {
            const data = await res.json();
            const meta = data.model ? 'via ' + data.model : '';
            copilotAppend('assistant', data.answer || '(empty response)', meta);
        }
    } catch (e) {
        typing.remove();
        copilotAppend('system', 'Network error: ' + e.message);
    } finally {
        Copilot.sendBtn.disabled = false;
    }
}

function aiStatusDetailDom(d) {
    const frag = document.createDocumentFragment();
    const llmOn = d.llm && d.llm.configured;
    const hfOn = d.hf && d.hf.configured;

    const row = (label, ok, okText, hint) => {
        const line = document.createElement('div');
        const strong = document.createElement('strong');
        strong.className = 'text-bright';
        strong.textContent = label + ' ';
        line.appendChild(strong);
        const state = document.createElement('span');
        state.className = ok ? 'text-accent' : 'risk-critical';
        state.textContent = ok ? okText : 'not configured';
        line.appendChild(state);
        if (!ok && hint) {
            const h = document.createElement('span');
            h.className = 'text-mute';
            h.textContent = ' — ' + hint;
            line.appendChild(h);
        } else if (ok && hint) {
            const h = document.createElement('span');
            h.className = 'text-mute';
            h.textContent = ' · ' + hint;
            line.appendChild(h);
        }
        return line;
    };

    frag.appendChild(row('LLM', llmOn, 'configured', d.llm && d.llm.model_default ? d.llm.model_default : 'set OR_API_KEY'));
    frag.appendChild(row('HuggingFace', hfOn, 'configured', hfOn ? 'cached model downloads' : 'set HF_TOKEN'));

    const features = d.features || {};
    const activeNames = Object.keys(features).filter(k => features[k]);
    const footer = document.createElement('div');
    footer.className = 'mt-2 text-mute';
    footer.style.fontSize = '0.72rem';
    footer.textContent = 'Active: ' + (activeNames.length ? activeNames.join(', ') : 'none');
    frag.appendChild(footer);
    return frag;
}

async function copilotCheckAI() {
    try {
        const res = await apiFetch('/api/system/ai-status');
        const d = await res.json();
        Copilot.aiReady = Boolean(d.llm && d.llm.configured);
        const badge = document.getElementById('aiBadge');
        const txt = document.getElementById('aiBadgeText');
        const detail = document.getElementById('aiStatusDetail');

        const hfOn = d.hf && d.hf.configured;
        const llmOn = d.llm && d.llm.configured;

        if (badge && txt) {
            if (llmOn || hfOn) {
                badge.classList.add('on');
                txt.textContent = llmOn && hfOn ? 'AI online' : (llmOn ? 'LLM online' : 'HF online');
            } else {
                badge.classList.remove('on');
                txt.textContent = 'AI offline';
            }
        }

        if (detail) {
            while (detail.firstChild) detail.removeChild(detail.firstChild);
            detail.appendChild(aiStatusDetailDom(d));
        }

        if (Copilot.status) {
            Copilot.status.textContent = llmOn
                ? 'Grounded on live crowd state · ' + (d.llm.model_default || 'LLM')
                : 'Offline — set OR_API_KEY in .env';
        }
    } catch { /* ignore */ }
}

document.addEventListener('DOMContentLoaded', () => {
    Copilot.panel = document.getElementById('copilotPanel');
    Copilot.fab = document.getElementById('copilotFab');
    Copilot.body = document.getElementById('copilotBody');
    Copilot.input = document.getElementById('copilotInput');
    Copilot.sendBtn = document.getElementById('copilotSend');
    Copilot.status = document.getElementById('copilotStatus');

    if (Copilot.fab) Copilot.fab.addEventListener('click', copilotToggle);
    const closeBtn = document.getElementById('copilotClose');
    if (closeBtn) closeBtn.addEventListener('click', copilotClose);

    if (Copilot.sendBtn) Copilot.sendBtn.addEventListener('click', () => copilotAsk(Copilot.input.value));
    if (Copilot.input) {
        Copilot.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                copilotAsk(Copilot.input.value);
            }
        });
    }

    document.querySelectorAll('.copilot-suggestion').forEach(btn => {
        btn.addEventListener('click', () => copilotAsk(btn.dataset.q || btn.textContent));
    });

    // C key toggles panel (unless user is typing)
    document.addEventListener('keydown', (e) => {
        if (e.key === 'c' && !e.ctrlKey && !e.metaKey) {
            const tag = (e.target && e.target.tagName) || '';
            if (tag === 'INPUT' || tag === 'TEXTAREA') return;
            copilotToggle();
        }
        if (e.key === 'Escape' && Copilot.open) copilotClose();
    });

    copilotCheckAI();
    setInterval(copilotCheckAI, 60000);
});
