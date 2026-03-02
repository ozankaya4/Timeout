/* =============================================================
   social.js — Timeout Social Features
   Handles: likes, bookmarks, status switching
   ============================================================= */

// ── Utility: get CSRF token from cookie ──────────────────────

function getCsrfToken() {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : '';
}

function postJSON(url, data) {
  return fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    body: JSON.stringify(data),
  }).then(r => r.json());
}


// ── Likes ─────────────────────────────────────────────────────

function initLikes() {
  document.querySelectorAll('.like-btn').forEach(btn => {
    const postId = btn.dataset.postId;

    // Fetch initial like state
    fetch(`/social/post/${postId}/like-status/`)
      .then(r => r.json())
      .then(data => {
        btn.dataset.liked = data.liked ? 'true' : 'false';
        btn.querySelector('.like-icon').textContent = data.liked ? '❤️' : '🤍';
        btn.querySelector('.like-count').textContent = data.count;
        btn.classList.toggle('liked', data.liked);
      })
      .catch(() => {});

    btn.addEventListener('click', function () {
      const liked = this.dataset.liked === 'true';

      postJSON(`/social/post/${postId}/like/`, {})
        .then(data => {
          if (data.success !== undefined ? data.success : true) {
            const nowLiked = !liked;
            this.dataset.liked = nowLiked ? 'true' : 'false';
            this.querySelector('.like-icon').textContent = nowLiked ? '❤️' : '🤍';
            this.querySelector('.like-count').textContent = data.count;
            this.classList.toggle('liked', nowLiked);
          }
        })
        .catch(err => console.error('Like error:', err));
    });
  });
}


// ── Bookmarks ─────────────────────────────────────────────────

function initBookmarks() {
  document.querySelectorAll('.bookmark-btn').forEach(btn => {
    const postId = btn.dataset.postId;

    // Fetch initial bookmark state
    fetch(`/social/post/${postId}/bookmark-status/`)
      .then(r => r.json())
      .then(data => {
        btn.dataset.bookmarked = data.bookmarked ? 'true' : 'false';
        btn.querySelector('.bookmark-icon').textContent = data.bookmarked ? '🔖' : '🏷️';
        btn.classList.toggle('bookmarked', data.bookmarked);
      })
      .catch(() => {});

    btn.addEventListener('click', function () {
      const bookmarked = this.dataset.bookmarked === 'true';

      postJSON(`/social/post/${postId}/bookmark/`, {})
        .then(data => {
          if (data.success !== undefined ? data.success : true) {
            const nowBookmarked = !bookmarked;
            this.dataset.bookmarked = nowBookmarked ? 'true' : 'false';
            this.querySelector('.bookmark-icon').textContent = nowBookmarked ? '🔖' : '🏷️';
            this.classList.toggle('bookmarked', nowBookmarked);
          }
        })
        .catch(err => console.error('Bookmark error:', err));
    });
  });
}


// ── Follow Button ─────────────────────────────────────────────

function initFollowButtons() {
  document.querySelectorAll('.follow-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const username  = this.dataset.username;
      const following = this.dataset.following === 'true';

      postJSON(`/social/follow/${username}/`, {})
        .then(data => {
          if (data.success !== undefined ? data.success : true) {
            const nowFollowing = !following;
            this.dataset.following = nowFollowing ? 'true' : 'false';
            this.textContent = nowFollowing ? 'Unfollow' : 'Follow';
          }
        })
        .catch(err => console.error('Follow error:', err));
    });
  });
}


// ── User Search ───────────────────────────────────────────────

function initUserSearch() {
  const input = document.getElementById('userSearchInput');
  const results = document.getElementById('userSearchResults');
  if (!input) return;

  // Attach to body so it's never clipped by parent overflow/stacking contexts
  document.body.appendChild(results);

  function positionDropdown() {
    const rect = input.getBoundingClientRect();
    results.style.position = 'fixed';
    results.style.top  = (rect.bottom + 4) + 'px';
    results.style.left = rect.left + 'px';
    results.style.width = rect.width + 'px';
    results.style.zIndex = '9999';
  }

  let timer;
  input.addEventListener('input', function () {
    clearTimeout(timer);
    const q = this.value.trim();
    if (!q) { results.hidden = true; results.innerHTML = ''; return; }

    timer = setTimeout(() => {
      fetch(`/social/search/?q=${encodeURIComponent(q)}`)
        .then(r => r.json())
        .then(data => {
          results.innerHTML = '';
          if (!data.users.length) {
            results.innerHTML = '<div class="search-no-results">No users found</div>';
          } else {
            data.users.forEach(u => {
              const avatar = u.profile_picture
                ? `<img src="${u.profile_picture}" class="search-avatar" alt="">`
                : `<div class="search-avatar search-avatar--initial">${u.username[0].toUpperCase()}</div>`;
              results.innerHTML += `
                <a href="${u.profile_url}" class="search-result-row">
                  ${avatar}
                  <div class="search-result-info">
                    <span class="search-result-name">${u.full_name}</span>
                    <span class="search-result-username">@${u.username}</span>
                  </div>
                  <span class="status-dot status-${u.status}"></span>
                </a>`;
            });
          }
          positionDropdown();
          results.hidden = false;
        })
        .catch(err => console.error('Search error:', err));
    }, 300);
  });

  document.addEventListener('click', e => {
    if (!input.contains(e.target) && !results.contains(e.target)) {
      results.hidden = true;
    }
  });

  input.addEventListener('focus', () => {
    if (results.innerHTML) { positionDropdown(); results.hidden = false; }
  });

  window.addEventListener('scroll', positionDropdown, { passive: true });
  window.addEventListener('resize', positionDropdown, { passive: true });
}


// ── Init ──────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  initLikes();
  initBookmarks();
  initFollowButtons();
  initUserSearch();
  initConversation();
});


// ── Conversation (chat page) ──────────────────────────────────

function initConversation() {
  const config = window.CONVO_CONFIG;
  if (!config) return; // only runs on conversation page

  const container = document.getElementById('message-container');
  const input     = document.getElementById('message-input');
  const sendBtn   = document.getElementById('send-btn');
  if (!container || !input || !sendBtn) return;

  // Track last message ID for polling
  let lastMessageId = 0;
  const existing = container.querySelectorAll('[data-message-id]');
  if (existing.length > 0) {
    lastMessageId = existing[existing.length - 1].dataset.messageId;
  }

  function scrollToBottom() {
    container.scrollTop = container.scrollHeight;
  }

  function appendMessage(msg) {
    // Remove empty state if present
    const empty = container.querySelector('.convo-empty');
    if (empty) empty.remove();

    const isMe = msg.is_me;
    const row  = document.createElement('div');
    row.className = `msg-bubble-row ${isMe ? 'msg-mine' : 'msg-theirs'}`;
    row.dataset.messageId = msg.id;
    row.innerHTML = `
      <div class="msg-bubble">
        <div class="msg-text">${msg.content}</div>
        <div class="msg-time">${msg.created_at}</div>
      </div>
    `;
    container.appendChild(row);
    lastMessageId = msg.id;
    scrollToBottom();
  }

  function sendMessage() {
    const content = input.value.trim();
    if (!content) return;

    fetch(config.sendUrl, {
      method: 'POST',
      headers: { 'X-CSRFToken': config.csrfToken },
      body: new URLSearchParams({ content })
    })
    .then(r => r.json())
    .then(data => {
      if (data.id) {
        appendMessage(data);
        input.value = '';
      }
    })
    .catch(err => console.error('Send error:', err));
  }

  sendBtn.addEventListener('click', sendMessage);
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') sendMessage();
  });

  // Poll for new messages every 3 seconds
  function pollMessages() {
    fetch(`${config.pollUrl}?last_id=${lastMessageId}`, {
      headers: { 'X-CSRFToken': config.csrfToken }
    })
    .then(r => r.json())
    .then(data => {
      data.messages.forEach(msg => {
        if (!msg.is_me) appendMessage(msg);
      });
    })
    .catch(err => console.error('Poll error:', err));
  }

  setInterval(pollMessages, 3000);
  scrollToBottom();
}