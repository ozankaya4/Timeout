(function() {
  var form = document.getElementById('settingsForm');
  var statusEl = document.getElementById('autosaveStatus');
  var statusText = document.getElementById('autosaveText');
  var saveUrl = '{% url "settings_save" %}';
  var csrfToken = '{{ csrf_token }}';
  var saveTimer = null;

  function showStatus(text, cls) {
    statusText.textContent = text;
    statusEl.className = 'stg-autosave stg-autosave--' + cls;
    statusEl.style.display = '';
    clearTimeout(statusEl._hideTimer);
    if (cls === 'saved') {
      statusEl._hideTimer = setTimeout(function() { statusEl.style.display = 'none'; }, 2000);
    }
  }

  function autoSave() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(doSave, 400);
  }

  function doSave() {
    showStatus('Saving...', 'saving');
    var data = new FormData(form);
    // Checkboxes: if unchecked, FormData won't include them and delete explicitly
    if (!form.querySelector('[name="notification_sounds"]').checked) {
      data.delete('notification_sounds');
    }
    if (!form.querySelector('[name="auto_online"]').checked) {
      data.delete('auto_online');
    }
    fetch(saveUrl, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken },
      body: data,
    })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (d.ok) showStatus('Saved', 'saved');
      else showStatus('Error', 'error');
    })
    .catch(function() { showStatus('Error', 'error'); });
  }

  // Listen to all form inputs
  form.querySelectorAll('input, select').forEach(function(el) {
    el.addEventListener('change', autoSave);
    if (el.type === 'range' || el.type === 'number') {
      el.addEventListener('input', autoSave);
    }
  });


  // Theme card active state + live preview
  document.querySelectorAll('.stg-theme-radio').forEach(function(radio) {
    radio.addEventListener('change', function() {
      document.querySelectorAll('.stg-theme-card').forEach(function(c) {
        c.classList.remove('stg-theme-card--active');
      });
      this.closest('.stg-theme-card').classList.add('stg-theme-card--active');

      var val = this.value;
      if (val === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        document.documentElement.dataset.themeSource = 'explicit';
      } else if (val === 'system') {
        var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
        document.documentElement.dataset.themeSource = 'system';
      } else {
        document.documentElement.setAttribute('data-theme', 'light');
        document.documentElement.dataset.themeSource = 'explicit';
      }
    });
  });

  // Colorblind mode active state + live preview
  document.querySelectorAll('.stg-radio-option input').forEach(function(radio) {
    radio.addEventListener('change', function() {
      this.closest('.stg-radio-group').querySelectorAll('.stg-radio-option').forEach(function(o) {
        o.classList.remove('stg-radio-option--active');
      });
      this.closest('.stg-radio-option').classList.add('stg-radio-option--active');
      document.documentElement.setAttribute('data-colorblind', this.value);
    });
  });
})();