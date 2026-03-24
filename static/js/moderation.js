// Admin moderation AJAX handlers (staff only)

function getCsrfToken() {
    const match = document.cookie.split(';')
        .map(c => c.trim())
        .find(c => c.startsWith('csrftoken='));
    return match ? decodeURIComponent(match.split('=')[1]) : '';
}

document.addEventListener('DOMContentLoaded', function () {
    const csrf = getCsrfToken();

    // Approve flag: delete the flagged post
    document.querySelectorAll('.btn-approve-flag').forEach(btn => {
        btn.addEventListener('click', function () {
            if (!confirm('Delete this post permanently?')) return;
            fetch(this.dataset.url, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrf },
            })
            .then(r => r.json())
            .then(data => { if (data.ok) this.closest('.flag-review-card').remove(); })
            .catch(err => console.error('Approve flag error:', err));
        });
    });

    // Deny flag: dismiss without removing the post
    document.querySelectorAll('.btn-deny-flag').forEach(btn => {
        btn.addEventListener('click', function () {
            fetch(this.dataset.url, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrf },
            })
            .then(r => r.json())
            .then(data => { if (data.ok) this.closest('.flag-review-card').remove(); })
            .catch(err => console.error('Deny flag error:', err));
        });
    });

    // Delete message in conversation
    document.querySelectorAll('.btn-delete-msg').forEach(btn => {
        btn.addEventListener('click', function () {
            if (!confirm('Delete this message permanently?')) return;
            fetch(this.dataset.url, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrf },
            })
            .then(r => r.json())
            .then(data => { if (data.ok) this.closest('.msg-bubble-row').remove(); })
            .catch(err => console.error('Delete message error:', err));
        });
    });
});
