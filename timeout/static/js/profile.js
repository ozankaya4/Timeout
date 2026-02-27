(() => {
  const cfg = document.getElementById('profile-status-config');
  if (!cfg) return;

  const url = cfg.dataset.updateUrl;
  const csrf = cfg.dataset.csrfToken;

  const navText = document.getElementById('nav-status-text');
  const navDot  = document.getElementById('nav-status-dot');
  const currentText = document.getElementById('current-status-display');

  function setNavDot(status) {
    if (!navDot) return;

    [...navDot.classList].forEach((cls) => {
      if (cls.startsWith('status-') && cls !== 'status-dot-nav') {
        navDot.classList.remove(cls);
      }
    });
    navDot.classList.add(`status-${status}`);
  }

  function setActiveStatusButton(status) {
    document.querySelectorAll('.status-btn').forEach((b) => {
      const isActive = b.dataset.status === status;
      b.classList.toggle('btn-primary', isActive);
      b.classList.toggle('btn-outline-secondary', !isActive);
    });
  }

  document.querySelectorAll('.status-btn').forEach((btn) => {
    btn.addEventListener('click', function () {
      const status = this.dataset.status;

      fetch(url, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrf,
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `status=${encodeURIComponent(status)}`
      })
        .then((r) => r.json())
        .then((data) => {
          if (!data?.status) return;

          if (currentText) currentText.textContent = data.status_display;

          setActiveStatusButton(data.status);

          if (navText) navText.textContent = data.status_display;
          setNavDot(data.status);
        });
    });
  });
})();