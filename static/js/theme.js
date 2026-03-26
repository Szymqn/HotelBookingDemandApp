(function () {
  function getPreferredTheme() {
    var storedTheme = localStorage.getItem('theme');
    if (storedTheme) {
      return storedTheme;
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function setTheme(theme) {
    document.documentElement.setAttribute('data-bs-theme', theme);
    if (window.Apex) {
      window.Apex.theme = { mode: theme };
      window.Apex.chart = { background: 'transparent' };
    }
  }

  function updateThemeIcon(theme) {
    var themeIcon = document.getElementById('themeIcon');
    if (themeIcon) {
      themeIcon.textContent = theme === 'dark' ? 'dark_mode' : 'light_mode';
    }
  }

  function notifyThemeChanged() {
    window.dispatchEvent(new Event('themeChanged'));
  }

  // Set theme as early as possible.
  setTheme(getPreferredTheme());

  window.getPreferredTheme = getPreferredTheme;
  window.setTheme = setTheme;
  window.updateThemeIcon = updateThemeIcon;

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function () {
    if (!localStorage.getItem('theme')) {
      var preferred = getPreferredTheme();
      setTheme(preferred);
      updateThemeIcon(preferred);
      notifyThemeChanged();
    }
  });

  document.addEventListener('DOMContentLoaded', function () {
    var currentTheme = document.documentElement.getAttribute('data-bs-theme');
    updateThemeIcon(currentTheme);

    var themeToggleBtn = document.getElementById('themeToggleBtn');
    if (themeToggleBtn) {
      themeToggleBtn.addEventListener('click', function () {
        var current = document.documentElement.getAttribute('data-bs-theme');
        var newTheme = current === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', newTheme);
        setTheme(newTheme);
        updateThemeIcon(newTheme);
        notifyThemeChanged();
      });
    }

    // Keep behavior from previous implementation: reload once to re-render chart colors.
    window.addEventListener('themeChanged', function () {
      setTimeout(function () {
        window.location.reload();
      }, 50);
    });
  });
})();

