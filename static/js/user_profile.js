(function () {
  if (typeof FOLLOWERS_URL === 'undefined' || typeof FOLLOWING_URL === 'undefined') return;

  function escapeHtml(str) {
    if (str == null) return '';
    return String(str)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  function _userAvatar(pic, username) {
    if (pic) return '<img src="' + escapeHtml(pic) + '" class="rounded-circle" width="40" height="40" style="object-fit:cover;">';
    return '<div class="rounded-circle bg-secondary text-white d-flex align-items-center justify-content-center fw-bold" style="width:40px;height:40px;">' +
      escapeHtml(username.charAt(0).toUpperCase() || '?') + '</div>';
  }

  function _userCard(u) {
    var username = u && u.username ? String(u.username) : '';
    var fullName = u && u.full_name ? String(u.full_name) : '';
    var pic = u && u.profile_picture ? String(u.profile_picture) : '';
    var href = '/social/user/' + encodeURIComponent(username) + '/';
    var fullNameHtml = fullName ? '<div class="text-muted small">' + escapeHtml(fullName) + '</div>' : '';
    return '<div class="user-item">' +
      '<a href="' + href + '" class="d-flex align-items-center gap-3 mb-3 text-decoration-none text-dark">' +
        _userAvatar(pic, username) +
        '<div><div class="fw-semibold">@' + escapeHtml(username) + '</div>' + fullNameHtml + '</div>' +
      '</a></div>';
  }

  function renderUserList(users) {
    if (!users || users.length === 0) return '<p class="text-center text-muted py-3">No users yet.</p>';
    return users.map(_userCard).join('');
  }

  function _attachSearchFilter(input, listEl) {
    if (!input) return;
    input.oninput = function () {
      var query = (this.value || '').toLowerCase().trim();
      listEl.querySelectorAll('.user-item').forEach(function (item) {
        var text = item.textContent.replace(/\s+/g, ' ').toLowerCase();
        item.style.display = text.includes(query) ? '' : 'none';
      });
    };
  }

  function setupModal(modalId, url, listId, searchAttr) {
    var modalEl = document.getElementById(modalId);
    if (!modalEl) return;

    modalEl.addEventListener('show.bs.modal', function () {
      var input = document.querySelector('[data-modal-search="' + searchAttr + '"]');
      if (input) { input.value = ''; input.oninput = null; }

      fetch(url)
        .then(function (r) { return r.json(); })
        .then(function (data) {
          var listEl = document.getElementById(listId);
          if (!listEl) return;
          listEl.innerHTML = renderUserList((data && data.users) ? data.users : []);
          _attachSearchFilter(input, listEl);
        });
    });
  }

  setupModal('followersModal', FOLLOWERS_URL, 'followers-list', 'followers-list');
  setupModal('followingModal', FOLLOWING_URL, 'following-list', 'following-list');
  setupModal('friendsModal', FRIENDS_URL, 'friends-list', 'friends-list');
})();
