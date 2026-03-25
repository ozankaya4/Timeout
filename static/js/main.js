/* Main JS Global settings & theme management */

(function() {
  'use strict';
  var html = document.documentElement;
  /* System theme listener */
  // If user chose "system", watch for OS-level changes
  var rawTheme = html.getAttribute('data-theme');
  function applySystemTheme(mq) {
    // Only act if the user's stored preference is "system"
    if (html.dataset.themeSource === 'system') {
      html.setAttribute('data-theme', mq.matches ? 'dark' : 'light');}}
  if (rawTheme === 'dark' || rawTheme === 'light') {
    // Explicit choice, mark so the listener doesn't override
    html.dataset.themeSource = 'explicit';
  } else {
    // "system" was resolved by inline script; mark for live updates
    html.dataset.themeSource = 'system';}

  var mq = window.matchMedia('(prefers-color-scheme: dark)');
  mq.addEventListener('change', function(e) { applySystemTheme(e); });

  /* Font size */
})();
