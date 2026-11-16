/* ideaLAB – CMS naslovne fotografije i filmska izmjena */
(() => {
  'use strict';
  const hero = document.querySelector('[data-idealab-hero]');
  if (!hero) return;
  const kind = hero.dataset.idealabHero;
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const toUrl = value => {
    try {
      if (typeof value !== 'string' || !value.trim()) return '';
      const u = new URL(value.trim(), document.baseURI);
      if (!['https:', 'http:'].includes(u.protocol)) return '';
      if (u.origin !== location.origin && u.hostname !== 'images.unsplash.com') return '';
      if (!/\.(jpe?g|png|webp|avif|gif)$/i.test(u.pathname) && u.hostname !== 'images.unsplash.com') return '';
      return u.href;
    } catch (_) { return ''; }
  };
  async function json(path) {
    const r = await fetch(path, {cache: 'no-store'});
    if (!r.ok) throw Error('HTTP ' + r.status);
    return r.json();
  }
  function load(url) {
    return new Promise((resolve, reject) => {
      const img = new Image(); img.alt = ''; img.decoding = 'async';
      img.onload = async () => { try { await img.decode(); } catch (_) {} resolve(img); };
      img.onerror = reject; img.src = url;
    });
  }
  if (kind !== 'slideshow') {
    json('naslovnice.json').then(async config => {
      const url = toUrl(config[kind]); if (!url) return;
      await load(url);
      hero.style.backgroundImage = 'linear-gradient(180deg,rgba(15,23,35,.34),rgba(15,23,35,.56)),url("' + url.replace(/"/g,'%22') + '")';
    }).catch(e => console.warn('Naslovnica usluge: ostaje zadana fotografija.', e));
    return;
  }
  const layers = [...hero.querySelectorAll('.hero-photo-layer')];
  const button = hero.querySelector('.hero-motion-toggle');
  if (layers.length !== 2) return;
  const key = 'idealab.hero.last.v3:' + location.pathname;
  let photos = [], index = -1, current = -1, timer, busy = false, paused = false;
  let nextImage = null, nextIndex = -1;
  const remember = url => { try { sessionStorage.setItem(key, url); } catch (_) {} };
  function cancel() { clearTimeout(timer); }
  function schedule() {
    cancel();
    if (!paused && !motion.matches && photos.length > 1) timer = setTimeout(advance, 9000);
  }
  function preloadNext() {
    nextIndex = (index + 1) % photos.length;
    nextImage = photos.length > 1 ? load(photos[nextIndex]).catch(() => null) : null;
  }
  async function show(i, img) {
    const incoming = current === 0 ? 1 : 0;
    const layer = layers[incoming];
    layer.classList.remove('is-current');
    layer.replaceChildren(img);
    // Force the opacity-zero state to be applied before crossfading.
    void layer.offsetWidth;
    layer.classList.add('is-current');
    if (current !== -1) layers[current].classList.remove('is-current');
    current = incoming; index = i; remember(photos[i]);
    preloadNext(); schedule();
  }
  async function advance() {
    if (busy || paused || motion.matches || photos.length < 2) return;
    busy = true;
    try {
      for (let offset=1; offset<photos.length; offset++) {
        const i = (index + offset) % photos.length;
        const img = i === nextIndex && nextImage ? await nextImage : await load(photos[i]).catch(()=>null);
        if (img) { if (!paused && !motion.matches) await show(i,img); return; }
      }
    } finally { busy = false; schedule(); }
  }
  if (button) button.addEventListener('click', () => {
    paused = !paused; hero.classList.toggle('motion-paused', paused);
    const label = paused ? 'Pokreni animaciju pozadine' : 'Pauziraj animaciju pozadine';
    button.textContent = paused ? '▶' : 'Ⅱ'; button.setAttribute('aria-pressed', String(paused));
    button.setAttribute('aria-label', label); button.title = label;
    paused ? cancel() : schedule();
  });
  motion.addEventListener('change', () => motion.matches ? cancel() : schedule());
  (async () => {
    try {
      const items = await json('pozadine.json');
      if (Array.isArray(items)) photos = [...new Set(items.filter(x=>x && x.aktivna===true).map(x=>toUrl(x.slika)).filter(Boolean))];
    } catch (e) { console.warn('Galerija nije učitana.',e); }
    if (!photos.length) photos = [toUrl('/images/paris-spring.jpeg')].filter(Boolean);
    let last=''; try { last=sessionStorage.getItem(key)||''; } catch (_) {}
    const start = (photos.indexOf(last)+1)%photos.length;
    for(let step=0;step<photos.length;step++) {
      const i=(start+step)%photos.length;
      const img=await load(photos[i]).catch(()=>null);
      if(img){await show(i,img);return;}
    }
    // A neutral background remains if none of the images can load.
  })();
})();
