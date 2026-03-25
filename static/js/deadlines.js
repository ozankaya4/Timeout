    function openAddEvent(dateStr) {
  document.getElementById('eventStart').value = dateStr + 'T09:00';
  document.getElementById('eventEnd').value = dateStr + 'T10:00';
  var modal = new bootstrap.Modal(document.getElementById('addEventModal'));
  modal.show();
}
document.addEventListener('DOMContentLoaded', function() {
   
  document.querySelectorAll('.dl-checkbox:not(.dl-checkbox--completed)').forEach(function(checkbox) {
    checkbox.addEventListener('change', function() {
      completeDeadline(this.dataset.eventId, this);
    });
  });

  // Mark incomplete — completed checkboxes
  document.querySelectorAll('.dl-checkbox--completed').forEach(function(checkbox) {
    checkbox.addEventListener('change', function() {
      if (!this.checked) {
        incompleteDeadline(this.dataset.eventId, this);
      }
    });
  });

});

function completeDeadline(eventId, checkbox) {
  var item = document.querySelector('[data-id="' + eventId + '"]');

  fetch('/deadlines/' + eventId + '/complete/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value
        || getCookie('csrftoken'),
      'Content-Type': 'application/json',
    },
  })
  .then(function(res) {
    if (!res.ok) throw new Error('Request failed');
    return res.json();
  })
  .then(function(data) {
    if (data.is_completed && item) {
      checkbox.disabled = true;
      item.classList.add('dl-item--completing');
      setTimeout(function() {
        item.remove();
        // Update tab count badge
        var panel = document.querySelector('.dl-tab-panel--active');
        if (panel) {
          var remaining = panel.querySelectorAll('.dl-item').length;
          var activeBtn = document.querySelector('.dl-tab-btn--active .dl-tab-count');
          if (activeBtn) activeBtn.textContent = remaining;
          if (remaining === 0) location.reload();
        }
      }, 400);
    }
  })
  .catch(function(err) {
    console.error('Complete failed:', err);
    checkbox.checked = false;
  });
}

function incompleteDeadline(eventId, checkbox) {
  var item = document.querySelector('[data-id="' + eventId + '"]');

  fetch('/deadlines/' + eventId + '/incomplete/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value
        || getCookie('csrftoken'),
      'Content-Type': 'application/json',
    },
  })
  .then(function(res) {
    if (!res.ok) throw new Error('Request failed');
    return res.json();
  })
  .then(function(data) {
    if (data.is_completed === false && item) {
      item.classList.add('dl-item--completing');
      setTimeout(function() {
        item.remove();
        if (document.querySelectorAll('.dl-item').length === 0) {
          location.reload();
        }
      }, 400);
    }
  })
  .catch(function(err) {
    console.error('Incomplete failed:', err);
    checkbox.checked = true;
  });
}

function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    document.cookie.split(';').forEach(function(cookie) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
      }
    });
  }
  return cookieValue;
}