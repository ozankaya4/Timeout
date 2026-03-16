let rsSuggestions = [];

function fetchRescheduleSuggestions() {
    rsShowLoading();

    fetch(window.RS_SUGGEST_URL, {
        method: 'POST',
        headers: { 'X-CSRFToken': window.AI_CSRF_TOKEN },
    })
    .then(r => r.json())
    .then(data => {
        if (!data.success) {
            rsShowError(data.error || 'Something went wrong.');
            rsShowStep1();
            return;
        }
        rsSuggestions = data.suggestions;
        rsRenderPreview(data.original, data.suggestions);
        rsShowStep2();
    })
    .catch(() => {
        rsShowError('Could not reach the server. Try again.');
        rsShowStep1();
    });
}

function rsRenderPreview(original, suggestions) {
    const tbody = document.getElementById('rs-preview-body');
    tbody.innerHTML = '';

    const originalMap = {};
    original.forEach(s => { originalMap[s.id] = s; });

    suggestions.forEach(s => {
        const old = originalMap[s.id];
        const oldTime = old ? fmtDatetime(old.start) + ' → ' + fmtTime(old.end) : '—';
        const newTime = fmtDatetime(s.start) + ' → ' + fmtTime(s.end);
        const changed = old && (old.start !== s.start);

        tbody.innerHTML += `
            <tr class="${changed ? 'table-warning' : ''}">
                <td>${s.title}</td>
                <td class="text-muted">${oldTime}</td>
                <td><strong>${newTime}</strong></td>
            </tr>`;
    });
}

function applyReschedule() {
    const btn = document.getElementById('rs-apply-btn');
    btn.disabled = true;
    btn.textContent = 'Applying…';

    const formData = new FormData();
    formData.append('sessions', JSON.stringify(rsSuggestions));
    formData.append('csrfmiddlewaretoken', window.AI_CSRF_TOKEN);

    fetch(window.RS_APPLY_URL, {
        method: 'POST',
        headers: { 'X-CSRFToken': window.AI_CSRF_TOKEN },
        body: formData,
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            bootstrap.Modal.getInstance(document.getElementById('rescheduleSessionsModal')).hide();
            window.location.reload();
        } else {
            rsShowError(data.error || 'Could not apply changes.');
            btn.disabled = false;
            btn.textContent = 'Apply Changes';
        }
    })
    .catch(() => {
        rsShowError('Could not reach the server.');
        btn.disabled = false;
        btn.textContent = 'Apply Changes';
    });
}

function rsShowStep1() {
    document.getElementById('rs-step-1').classList.remove('d-none');
    document.getElementById('rs-step-2').classList.add('d-none');
    document.getElementById('rs-loading').classList.add('d-none');
    document.getElementById('rs-suggest-btn').classList.remove('d-none');
    document.getElementById('rs-back-btn').classList.add('d-none');
    document.getElementById('rs-apply-btn').classList.add('d-none');
    document.getElementById('rs-error').classList.add('d-none');
}

function rsShowStep2() {
    document.getElementById('rs-step-1').classList.add('d-none');
    document.getElementById('rs-step-2').classList.remove('d-none');
    document.getElementById('rs-loading').classList.add('d-none');
    document.getElementById('rs-suggest-btn').classList.add('d-none');
    document.getElementById('rs-back-btn').classList.remove('d-none');
    document.getElementById('rs-apply-btn').classList.remove('d-none');
}

function rsShowLoading() {
    document.getElementById('rs-step-1').classList.add('d-none');
    document.getElementById('rs-step-2').classList.add('d-none');
    document.getElementById('rs-loading').classList.remove('d-none');
    document.getElementById('rs-suggest-btn').classList.add('d-none');
    document.getElementById('rs-error').classList.add('d-none');
}

function rsShowError(msg) {
    const el = document.getElementById('rs-error');
    el.textContent = msg;
    el.classList.remove('d-none');
}

function fmtDatetime(str) {
    if (!str) return '—';
    const d = new Date(str);
    return d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })
        + ' ' + fmtTime(str);
}

function fmtTime(str) {
    if (!str) return '—';
    return str.slice(11, 16);
}

document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('rescheduleSessionsModal');
    if (modal) {
        modal.addEventListener('hidden.bs.modal', rsShowStep1);
    }
});
