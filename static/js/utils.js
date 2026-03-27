/**
 * Shared Utilities
 * Common helpers used across multiple JS modules.
 */

/**
 * Retrieve CSRF token from browser cookies for secure Django form submissions.
 */
function getCSRFToken() {
    const match = document.cookie.split(';')
        .map(c => c.trim())
        .find(c => c.startsWith('csrftoken='));
    return match ? decodeURIComponent(match.split('=')[1]) : '';
}

/**
 * Perform a POST request with CSRF token, returning parsed JSON.
 * @param {string} url - The endpoint URL.
 * @param {Object} [options] - Optional { headers, body }.
 * @returns {Promise<Object>} Parsed JSON response.
 */
function postJSON(url, { headers = {}, body } = {}) {
    return fetch(url, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCSRFToken(), ...headers },
        body,
    }).then(r => r.json());
}
