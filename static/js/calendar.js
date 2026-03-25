function openAddEvent(dateStr) {
    document.getElementById('eventStart').value = dateStr + 'T09:00';
    document.getElementById('eventEnd').value = dateStr + 'T10:00';
    var modal = new bootstrap.Modal(document.getElementById('addEventModal'));
    modal.show();
}

(function () {
    const params = new URLSearchParams(window.location.search);
    const openId = params.get("open_event");
    if (openId) {
        const chip = document.querySelector(`[data-event-id="${openId}"]`);
        if (chip) {
            chip.scrollIntoView({ behavior: "smooth", block: "center" });
            chip.classList.add("event-highlight");
            setTimeout(() => chip.classList.remove("event-highlight"), 2500);
            chip.click();
        }
    }
    if (!openId) return;
    window.addEventListener('load', function () {
        const chip = document.querySelector(`[data-event-id="${openId}"]`);
        if (chip) chip.click();
    });
})();

window.AI_ADD_URL = document.querySelector('meta[name="ai-add-url"]').content;
window.AI_CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]').content;
window.SP_PLAN_URL = document.querySelector('meta[name="sp-plan-url"]').content;
window.SP_CONFIRM_URL = document.querySelector('meta[name="sp-confirm-url"]').content;
window.RESCHEDULE_URL = document.querySelector('meta[name="reschedule-url"]').content;
window.RESCHEDULE_CANCEL_URL_TPL = '/calendar/{id}/cancel/';
window.EVENT_CREATE_URL = document.querySelector('meta[name="event-create-url"]').content;
window.RS_SUGGEST_URL = document.querySelector('meta[name="rs-suggest-url"]').content;
window.RS_APPLY_URL = document.querySelector('meta[name="rs-apply-url"]').content;

function openDayEvents(dateStr, dateLabel, el) {
    const cell = el.closest('td');
    const chips = cell.querySelectorAll('.cal-chip');

    document.getElementById('dayEventsModalTitle').textContent = dateLabel;

    const body = document.getElementById('dayEventsModalBody');
    body.innerHTML = '';

    chips.forEach(chip => {
        const item = document.createElement('div');
        item.className = 'day-modal-event-item';

        const title = chip.dataset.eventTitle || chip.textContent.trim();
        const start = chip.dataset.eventStart || '';
        const end = chip.dataset.eventEnd || '';
        const eventClass = [...chip.classList]
            .find(c => c.startsWith('cal-chip--') && c !== 'cal-chip--conflict') || '';

        item.innerHTML = `
        <div class="day-modal-event ${eventClass}">
            <div class="day-modal-event-title">${title}</div>
            <div class="day-modal-event-time">${start} → ${end}</div>
        </div>
        `;

        item.addEventListener('click', () => {
            bootstrap.Modal.getInstance(document.getElementById('dayEventsModal'))?.hide();
            setTimeout(() => chip.click(), 300);
        });

        body.appendChild(item);
    });

    new bootstrap.Modal(document.getElementById('dayEventsModal')).show();
}

// Highlight currently ongoing events
document.querySelectorAll('.cal-chip').forEach(chip => {
    const status = chip.getAttribute('data-event-status');
    if (status === 'Ongoing') {
        chip.classList.add('cal-chip--ongoing');
    }
});