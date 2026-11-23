// Sari-Sari Tech appearance preferences
(() => {
  const userKey = document.body.dataset.themeUser || 'guest';
  const themeStorageKey = 'sari-sari-theme-' + userKey;
  const colorStorageKey = 'sari-sari-accent-' + userKey;
  const themes = ['light', 'dark', 'contrast', 'beige'];

  function applyTheme(theme) {
    const safeTheme = themes.includes(theme) ? theme : 'light';
    document.documentElement.dataset.theme = safeTheme;
    const selector = document.getElementById('theme-select');
    if (selector) selector.value = safeTheme;
  }

  function applyAccent(color) {
    if (!/^#[0-9a-fA-F]{6}$/.test(color || '')) return;
    document.documentElement.style.setProperty('--red', color);
    document.documentElement.style.setProperty('--red-dark', 'color-mix(in srgb, ' + color + ' 78%, black)');
    const picker = document.getElementById('accent-color');
    if (picker) picker.value = color;
  }

  let savedTheme = 'light';
  let savedAccent = '#b51f32';
  try {
    savedTheme = localStorage.getItem(themeStorageKey) || 'light';
    savedAccent = localStorage.getItem(colorStorageKey) || '#b51f32';
  } catch (error) {
    // The default appearance remains available if browser storage is disabled.
  }
  applyTheme(savedTheme);
  applyAccent(savedAccent);

  document.addEventListener('DOMContentLoaded', () => {
    const themeSelector = document.getElementById('theme-select');
    const colorPicker = document.getElementById('accent-color');

    if (themeSelector) {
      themeSelector.addEventListener('change', () => {
        applyTheme(themeSelector.value);
        try { localStorage.setItem(themeStorageKey, themeSelector.value); } catch (error) {}
      });
    }

    if (colorPicker) {
      colorPicker.addEventListener('input', () => {
        applyAccent(colorPicker.value);
        try { localStorage.setItem(colorStorageKey, colorPicker.value); } catch (error) {}
      });
    }

    const photoInput = document.querySelector('input[name="photos"]');
    const photoCount = document.getElementById('photo-count');
    if (photoInput && photoCount) {
      photoInput.addEventListener('change', () => {
        const count = photoInput.files.length;
        photoCount.textContent = count ? `${count} photo(s) selected.` : 'No photos selected.';
        if (count > 5) {
          photoCount.textContent = 'Please select no more than five photos.';
          photoInput.value = '';
        }
      });
    }
  });
})();
