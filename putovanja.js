/* IDEALAB: učitavanje ponuda iz jednostavne podatkovne datoteke.
 * Uređivanje sadržaja: Pages CMS -> putovanja.json
 * Ne mijenjati ovaj kod pri dodavanju novih putovanja.
 */
(() => {
  'use strict';
  const featuredGrid = document.getElementById('izdvojene-ponude');
  const allGrid = document.getElementById('sva-putovanja');
  const emptyMessage = document.getElementById('nema-putovanja');
  const filterButtons = [...document.querySelectorAll('.filter-btn')];
  if (!featuredGrid || !allGrid) return;

  const categoryLabels = {
    europa:'Europa', hrvatska:'Hrvatska', advent:'Advent',
    citybreak:'City break', tematske:'Tematske ture', daleka:'Daleka putovanja'
  };
  let activeFilter = 'all';
  let published = [];
  const txt = (x) => typeof x === 'string' ? x.trim() : '';

  // Putanja iz CMS-a; nikad ne dopuštamo javascript: i druge opasne protokole.
  function mediaUrl(value, wanted) {
    const path = txt(value);
    if (!path) return '';
    try {
      const url = new URL(path, document.baseURI);
      if (url.protocol !== 'https:' && url.protocol !== 'http:') return '';
      if (wanted === 'pdf' && !url.pathname.toLowerCase().endsWith('.pdf')) return '';
      return url.href;
    } catch (_) { return ''; }
  }

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function makeCard(trip, isFeatured) {
    const outer = el('article', `${isFeatured ? 'offer-card rounded-xl shadow-lg transition duration-300' : 'destination-item rounded-lg shadow-md'} idealab-card bg-white overflow-hidden`);
    outer.dataset.category = txt(trip.kategorija);
    const cover = el('div', 'relative');
    const image = el('img', `w-full ${isFeatured ? 'h-64' : 'h-48'} object-cover`);
    image.alt = txt(trip.naslov) || 'Fotografija putovanja';
    image.loading = 'lazy';
    image.decoding = 'async';
    image.src = mediaUrl(trip.slika, 'image') || '/images/educational_travel_world.jpg';
    image.addEventListener('error', () => {
      if (!image.src.endsWith('/images/educational_travel_world.jpg')) image.src = '/images/educational_travel_world.jpg';
    });
    cover.append(image);
    const category = el('span', isFeatured
      ? 'absolute top-4 right-4 bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-medium'
      : 'bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded',
      categoryLabels[trip.kategorija] || 'Putovanje');
    if (isFeatured) cover.append(category);
    outer.append(cover);

    const body = el('div', `${isFeatured ? 'p-6' : 'p-4'} idealab-card-body`);
    if (isFeatured) {
      body.append(el('h3', 'idealab-card-title text-xl font-bold mb-2', txt(trip.naslov)));
    } else {
      const heading = el('div', 'flex justify-between items-start gap-2 mb-2');
      heading.append(el('h3', 'idealab-card-title text-lg font-bold', txt(trip.naslov)), category);
      body.append(heading);
    }
    if (txt(trip.termin)) body.append(el('p', 'text-blue-700 font-semibold text-sm mb-2', txt(trip.termin)));
    const description = el('p', `idealab-card-desc text-gray-600 ${isFeatured ? 'mb-4' : 'text-sm mb-3'}`, txt(trip.opis));
    description.title = txt(trip.opis); // Puni opis dostupan prelaskom miša.
    body.append(description);

    const actions = el('div', 'idealab-card-actions');
    actions.append(el('span', isFeatured ? 'text-2xl font-bold text-blue-600' : 'text-blue-600 font-bold', txt(trip.cijena) || 'Cijena na upit'));
    const pdf = mediaUrl(trip.pdf, 'pdf');
    const a = el('a', 'text-blue-800 font-medium hover:text-blue-600 inline-flex items-center gap-2', pdf ? 'PDF program ' : 'Pošaljite upit ');
    a.href = pdf || '#kontakt';
    if (pdf) { a.target = '_blank'; a.rel = 'noopener noreferrer'; }
    const arrow = el('i', 'fas fa-arrow-right');
    arrow.setAttribute('aria-hidden', 'true');
    a.append(arrow);
    actions.append(a);
    body.append(actions);
    outer.append(body);
    return outer;
  }

  function drawCards(container, trips, featured) {
    container.replaceChildren();
    for (const item of trips) container.append(makeCard(item, featured));
  }
  function render() {
    const displayed = published.filter((t) => activeFilter === 'all' || t.kategorija === activeFilter);
    drawCards(allGrid, displayed, false);
    emptyMessage.classList.toggle('hidden', displayed.length > 0);
  }
  filterButtons.forEach((button) => {
    button.addEventListener('click', () => {
      activeFilter = button.dataset.filter || 'all';
      filterButtons.forEach(b => b.classList.toggle('active', b === button));
      render();
    });
  });

  fetch('./putovanja.json', { cache:'no-store' })
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then((data) => {
      if (!Array.isArray(data)) throw new Error('Podaci nisu popis putovanja');
      published = data.filter(t => t && t.vidljivo === true && txt(t.naslov));
      const featured = published.filter(t => t.izdvojeno === true);
      drawCards(featuredGrid, featured, true);
      if (!featured.length) featuredGrid.append(el('p', 'text-gray-600', 'Za aktualne ponude slobodno nam se javite.'));
      render();
    })
    .catch((error) => {
      console.error('Idealab: putovanja nisu učitana:', error);
      featuredGrid.replaceChildren(el('p', 'text-gray-600', 'Ponude se trenutačno ne mogu učitati. Molimo javite nam se putem kontakta.'));
      allGrid.replaceChildren();
      emptyMessage.textContent = 'Ponude se trenutačno ne mogu učitati. Molimo javite nam se putem kontakta.';
      emptyMessage.classList.remove('hidden');
    });
})();
