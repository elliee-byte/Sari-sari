document.addEventListener('DOMContentLoaded', () => {
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
