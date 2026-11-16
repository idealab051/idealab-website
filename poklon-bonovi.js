/* Idealab gift gallery: select, expand and preview without trackers or embeds. */
(() => {
  'use strict';
  const select = document.getElementById('gift-design');
  const cards = Array.from(document.querySelectorAll('.gift-card'));
  const feedback = document.getElementById('gift-selected-info');
  const expand = document.getElementById('gift-show-all');
  const extras = Array.from(document.querySelectorAll('.gift-extra'));
  const dialog = document.getElementById('gift-preview');
  const previewImage = document.getElementById('gift-preview-image');
  const previewCaption = document.getElementById('gift-preview-caption');
  const choosePreview = document.getElementById('gift-use-preview');
  let previewDesign = '';
  let showingAll = false;
  function showAll(flag) {
    showingAll = flag;
    extras.forEach(card => { card.hidden = !flag; });
    if (expand) {
      expand.setAttribute('aria-expanded', String(flag));
      expand.innerHTML = flag ? 'Prikažite manje dizajna <span aria-hidden="true">↑</span>' : `Pogledajte svih ${cards.length} dizajna <span aria-hidden="true">↓</span>`;
    }
  }
  function sync() {
    const selected = select.value;
    cards.forEach(card => {
      const active = card.dataset.design === selected;
      card.classList.toggle('is-selected', active);
      card.querySelector('.gift-select')?.setAttribute('aria-pressed', String(active));
    });
    const chosen = cards.find(card => card.dataset.design === selected);
    if (chosen && chosen.hidden) showAll(true);
    feedback.textContent = selected ? `Odabrali ste: ${selected}. Podatke možete unijeti u obrazac ispod.` : 'Dizajn možete izabrati i klikom na karticu u galeriji.';
  }
  select?.addEventListener('change', sync);
  document.querySelectorAll('[data-select-design]').forEach(button => button.addEventListener('click', () => {
    select.value = button.dataset.selectDesign;
    sync();
    document.getElementById('personalizacija')?.scrollIntoView({behavior:'smooth',block:'start'});
    select.focus({preventScroll:true});
  }));
  expand?.addEventListener('click', () => showAll(!showingAll));
  document.querySelectorAll('[data-preview]').forEach(button => button.addEventListener('click', () => {
    if (!dialog || typeof dialog.showModal !== 'function') return;
    previewDesign = button.closest('.gift-card')?.dataset.design || '';
    previewImage.src = button.dataset.preview;
    previewImage.alt = `Uvećani poklon bon – ${button.dataset.previewAlt || ''}`;
    previewCaption.textContent = previewDesign;
    dialog.showModal();
  }));
  choosePreview?.addEventListener('click', () => {
    if (!previewDesign) return;
    select.value = previewDesign;
    sync();
    dialog.close();
    document.getElementById('personalizacija')?.scrollIntoView({behavior:'smooth',block:'start'});
    select.focus({preventScroll:true});
  });
  dialog?.addEventListener('click', event => {
    if (event.target === dialog) dialog.close();
  });
  const previewNote = document.getElementById('gift-preview-info');
  if (previewNote && location.hostname.endsWith('.pages.dev')) previewNote.hidden = false;
})();
