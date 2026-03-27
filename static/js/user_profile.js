/**
 * User Profile Modals
 * Handles user list rendering and search functionality for followers, following, and friends modals.
 */

(function () {
  if (typeof FOLLOWERS_URL === 'undefined' || typeof FOLLOWING_URL === 'undefined') return;

  /**
   * Escape HTML special characters to prevent XSS vulnerabilities.
   */
  function escapeHtml(str) {
    if (str == null) return '';
    return String(str)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  /**
   * Generate complete user card HTML with avatar, username, and full name.
   */
  function _userCard(u) {
    var username = u && u.username ? String(u.username) : '';
    var fullName = u && u.full_name ? String(u.full_name) : '';
    var pic = u && u.profile_picture ? String(u.profile_picture) : '';
    var href = '/social/user/' + encodeURIComponent(username) + '/';
    var fullNameHtml = fullName ? '<div class="text-muted small">' + escapeHtml(fullName) + '</div>' : '';
    return '<div class="user-item">' +
      '<a href="' + href + '" class="d-flex align-items-center gap-3 mb-3 text-decoration-none text-dark">' +
        userAvatarHtml(pic, username) +
        '<div><div class="fw-semibold">@' + escapeHtml(username) + '</div>' + fullNameHtml + '</div>' +
      '</a></div>';
  }

  /**
   * Render HTML for complete user list or empty state message.
   */
  function renderUserList(users) {
    if (!users || users.length === 0) return '<p class="text-center text-muted py-3">No users yet.</p>';
    return users.map(_userCard).join('');
  }

  /**
   * Configure modal to fetch and display user list with search functionality on open.
   */
  function setupModal(modalId, url, listId, searchAttr) {
    var modalEl = document.getElementById(modalId);
    if (!modalEl) return;

    modalEl.addEventListener('show.bs.modal', function () {
      var input = document.querySelector('[data-modal-search="' + searchAttr + '"]');
      if (input) { input.value = ''; input.oninput = null; }

      getJSON(url)
        .then(function (data) {
          var listEl = document.getElementById(listId);
          if (!listEl) return;
          listEl.innerHTML = renderUserList((data && data.users) ? data.users : []);
          attachUserSearchFilter(input, listEl);
        });
    });
  }

  setupModal('followersModal', FOLLOWERS_URL, 'followers-list', 'followers-list');
  setupModal('followingModal', FOLLOWING_URL, 'following-list', 'following-list');
  setupModal('friendsModal', FRIENDS_URL, 'friends-list', 'friends-list');
})();

/**
 * Initialize block/unblock button handlers on user profile.
 * Toggles block status via API, updates button text, styling, and reloads page.
 */
document.querySelectorAll('.block-btn').forEach(btn => {
  btn.addEventListener('click', function () {
    const username = this.dataset.username;
    const isBlocked = this.dataset.blocked === 'true';
    this.disabled = true;
    this.textContent = isBlocked ? 'Unblocking…' : 'Blocking…';

    postJSON(`/social/user/${username}/block/`)
      .then(data => {
        if (data.blocked === true) {
          this.dataset.blocked = 'true';
          this.textContent = 'Unblock';
          this.classList.remove('btn-outline-danger');
          this.classList.add('btn-outline-secondary');
          location.reload();
        } else {
          this.dataset.blocked = 'false';
          this.textContent = 'Block';
          this.classList.remove('btn-outline-secondary');
          this.classList.add('btn-outline-danger');
          location.reload();
        }
      })
      .catch(() => {
        this.disabled = false;
        this.textContent = isBlocked ? 'Unblock' : 'Block';
      });
  });
});