// CMS-selected files; keep initial links usable even if JavaScript is unavailable.
(async () => {
  const keys = ['uvjeti', 'obrazac', 'osiguranje', 'arhiva'];
  const error = document.getElementById('doc-error');
  try {
    const response = await fetch('pravna-dokumentacija.json', {cache: 'no-cache'});
    if (!response.ok) throw new Error('Pravna dokumentacija nije dostupna');
    const data = await response.json();
    const updates = keys.map(key => {
      const path = data[key + '_pdf'];
      const opis = data[key + '_opis'];
      if (typeof path !== 'string' || !path.trim() || typeof opis !== 'string' || !opis.trim()) throw new Error('Nepotpuni podaci');
      const url = new URL(path, document.baseURI);
      if (url.origin !== location.origin || !url.pathname.startsWith('/dokumenti/') || !url.pathname.toLowerCase().endsWith('.pdf') || url.search || url.hash) throw new Error('Neispravna poveznica');
      return {key, url, opis};
    });
    for (const {key, url, opis} of updates) {
      document.getElementById(key + '-pdf').href = url.href;
      document.getElementById(key + '-opis').textContent = opis;
    }
  } catch (e) { error.hidden = false; }
})();
