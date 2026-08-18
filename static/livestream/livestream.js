document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('stream-modal');
  const player = document.getElementById('stream-modal-player');
  const title = document.getElementById('stream-modal-title');
  const closeButton = document.getElementById('stream-modal-close');
  if (!modal || !player || !title || !closeButton) return;

  let opener = null;
  const closeModal = () => {
    player.src = '';
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('modal-open');
    if (opener) opener.focus();
  };
  document.querySelectorAll('.previous-stream-button').forEach((button) => {
    button.addEventListener('click', () => {
      const embedUrl = button.dataset.embedUrl;
      if (!embedUrl) return;
      opener = button;
      title.textContent = button.dataset.title || 'Recording';
      player.src = embedUrl;
      modal.classList.add('is-open');
      modal.setAttribute('aria-hidden', 'false');
      document.body.classList.add('modal-open');
      closeButton.focus();
    });
  });
  document.querySelectorAll('.previous-stream-card').forEach((card) => {
    card.addEventListener('click', (event) => {
      if (event.target.closest('.previous-stream-button')) return;
      const embedUrl = card.dataset.embedUrl;
      if (!embedUrl) return;
      opener = null;
      title.textContent = card.dataset.title || 'Recording';
      player.src = embedUrl;
      modal.classList.add('is-open');
      modal.setAttribute('aria-hidden', 'false');
      document.body.classList.add('modal-open');
      closeButton.focus();
    });
  });
  closeButton.addEventListener('click', closeModal);
  modal.addEventListener('click', (event) => { if (event.target === modal) closeModal(); });
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape' && modal.classList.contains('is-open')) closeModal(); });
});
