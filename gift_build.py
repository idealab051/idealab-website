"""Gift vouchers: add a CMS-managed gallery/page and gentle homepage invitation.
Only appends to the already-generated Cloudflare Pages /dist output.
No changes to travel or blog source data.
"""
from pathlib import Path
from html import escape
import json, re

FORM_ACTION = 'https://formspree.io/f/moveypzr'
SITE_URL = 'https://idealab.hr/poklon-bonovi.html'


def esc(value):
    return escape(str(value or ''), quote=True)


def make(root, out, page):
    src = root / 'poklon-bonovi.json'
    if not src.exists():
        raise ValueError('Nedostaje poklon-bonovi.json; dodajte datoteku iz paketa.')
    entries = json.loads(src.read_text(encoding='utf-8-sig'))
    if not isinstance(entries, list):
        raise ValueError('poklon-bonovi.json mora biti lista')
    vouchers = []
    for entry in entries:
        if not isinstance(entry, dict) or entry.get('aktivan') is not True:
            continue
        name = str(entry.get('naziv', '')).strip()
        image = str(entry.get('slika', '')).strip()
        if not name or not re.fullmatch(r'/images/[a-zA-Z0-9_./-]+\.(?:webp|png|jpe?g)', image, flags=re.I):
            continue
        if '..' in image.split('/'):
            continue
        if not (root / image.lstrip('/')).is_file():
            raise ValueError('Nedostaje slika poklon bona: ' + image)
        identifier = str(len(vouchers) + 1).zfill(2)
        vouchers.append({'id': identifier, 'name': name, 'image': image})
    if not vouchers:
        raise ValueError('Nema aktivnih vizuala poklon bonova; označite barem jedan u CMS-u')

    cards = []
    options = ['<option value="">Odaberite dizajn iz galerije</option>']
    for i, v in enumerate(vouchers):
        code = 'Dizajn '+v['id']+' – '+v['name']
        options.append('<option value="'+esc(code)+'">'+esc(code)+'</option>')
        attr = ' hidden' if i >= 8 else ''
        extra = ' gift-extra' if i >= 8 else ''
        cards.append(f'''<article class="gift-card{extra}" data-design="{esc(code)}"{attr}>
          <button type="button" class="gift-image-button" data-preview="{esc(v['image'])}" data-preview-alt="{esc(v['name'])}" aria-label="Uvećajte dizajn {esc(v['name'])}">
            <img src="{esc(v['image'])}" alt="Poklon bon – {esc(v['name'])}" loading="lazy" decoding="async" width="800" height="566"><span class="gift-magnify" aria-hidden="true">↗</span>
          </button>
          <div class="gift-card-body"><div><span class="gift-number">DIZAJN {esc(v['id'])}</span><h3>{esc(v['name'])}</h3></div>
          <button type="button" class="gift-select" data-select-design="{esc(code)}" aria-label="Odaberite dizajn {esc(v['name'])}" aria-pressed="false">Odaberi <span aria-hidden="true">✓</span></button></div>
        </article>''')
    options.append('<option value="Vlastita fotografija – poseban dizajn">Želim bon s vlastitom fotografijom</option>')

    main = f'''<main id="glavni-sadrzaj" class="gift-page">
    <section class="gift-hero" aria-labelledby="gift-title"><div class="gift-hero-inner">
      <div class="gift-hero-copy">
        <p class="gift-eyebrow">IDEALAB · POKLON BONOVI</p>
        <h1 id="gift-title">Poklonite putovanje.<br><span>Poklonite uspomene.</span></h1>
        <p class="gift-lead">Neki pokloni ostaju u sjećanju mnogo dulje od trenutka kada ih darujemo.</p>
        <p>Za rođendan, diplomu, vjenčanje, veliku obljetnicu, odlazak u mirovinu ili jednostavno za nekoga tko zaslužuje nešto posebno.</p>
        <p>Ne morate znati kamo će otputovati. Dovoljno je poželjeti im pokloniti nešto što će dugo pamtiti.</p>
        <p class="gift-promise">Vi birate vrijednost, dizajn i osobnu posvetu. Mi ćemo vaš poklon pretvoriti u jedinstvenu putničku priču.</p>
        <a class="gift-primary" href="#dizajni">Otkrijte naše poklon bonove <span aria-hidden="true">↓</span></a>
      </div>
      <div class="gift-hero-art" aria-hidden="true">
         <img class="gift-hero-card gift-hero-back" src="{esc(vouchers[1]['image'] if len(vouchers)>1 else vouchers[0]['image'])}" alt="" loading="eager">
         <img class="gift-hero-card gift-hero-front" src="{esc(vouchers[4]['image'] if len(vouchers)>4 else vouchers[0]['image'])}" alt="" loading="eager">
         <span class="gift-art-caption">Vaš poklon. Vaša priča.</span>
      </div>
    </div></section>

    <section class="gift-section gift-designs" id="dizajni" aria-labelledby="gift-gallery-heading">
      <div class="gift-container">
        <div class="gift-section-heading"><span class="gift-kicker">SVAKI POKLON IMA SVOJ KARAKTER</span><h2 id="gift-gallery-heading">Odaberite priču u koju ćemo upisati vašu posvetu.</h2>
          <p>Od pogleda kroz prozor aviona do starih putničkih karata – pronađite dizajn koji najbolje pristaje osobi kojoj darujete.</p>
        </div>
        <div class="gift-gallery" id="gift-gallery">{''.join(cards)}</div>
        <div class="gift-gallery-actions"><button type="button" class="gift-outline" id="gift-show-all" aria-controls="gift-gallery" aria-expanded="false">Pogledajte svih {len(vouchers)} dizajna <span aria-hidden="true">↓</span></button></div>
        <p class="gift-fineprint">Prikazani iznosi, imena i datumi na dizajnima služe kao primjeri. Vrijednost i podatke za vaš bon prilagođavamo prema narudžbi.</p>
      </div>
    </section>

    <section class="gift-photo-section" aria-labelledby="gift-photo-title"><div class="gift-container gift-photo-flex"><div class="gift-photo-mark" aria-hidden="true">✦</div>
        <div><span class="gift-kicker">ZA ONE NAJOSOBNIJE POKLONE</span><h2 id="gift-photo-title">A možda uspomena već ima svoju fotografiju?</h2>
          <p>Možemo pripremiti i poklon bon s vašom fotografijom. Odaberite tu mogućnost u obrascu, a fotografiju nam jednostavno pošaljite e-mailom na <a href="mailto:info@idealab.hr?subject=Fotografija%20za%20poklon%20bon">info@idealab.hr</a>, uz ime naručitelja.</p>
        </div></div></section>

    <section class="gift-section gift-personal-section" id="personalizacija" aria-labelledby="gift-form-heading"><div class="gift-container gift-form-layout">
      <div class="gift-form-aside"><span class="gift-kicker">POTPUNO OSOBNO</span><h2 id="gift-form-heading">Učinimo vaš poklon osobnim.</h2>
        <p>Možda ga daruje cijelo društvo, obitelj ili netko tko je samo poželio razveseliti dragu osobu. Svaki je razlog dobar da nastane nova uspomena.</p>
        <p class="gift-saying">Ne znate što napisati?<br><strong>Prepustite to nama.</strong></p>
        <p>Rado ćemo vam pomoći osmisliti posvetu za posebnu prigodu.</p>
        <div class="gift-how"><h3>Kako to funkcionira?</h3><ol><li>Odaberite dizajn i upišite svoje želje.</li><li>Poslat ćemo vam potvrdu i podatke za uplatu.</li><li>Nakon uplate personalizirat ćemo poklon bon i dostaviti ga e-mailom u PDF formatu.</li></ol></div>
      </div>
      <div class="gift-form-card">
        <h3>Ispričajte nam svoju ideju</h3><p class="gift-form-intro">Ovo je neobvezujući zahtjev – plaćanje nije potrebno prilikom ispunjavanja obrasca.</p>
        <form id="gift-form" data-idealab-form="poklon-bon" data-status="gift-form-status" action="{FORM_ACTION}" method="POST">
          <input type="hidden" name="vrsta_upita" value="Poklon bon – zahtjev za personalizaciju"><input type="hidden" name="_subject" value="Idealab – novi upit za poklon bon">
          <div class="gift-field"><label for="gift-design">Koji vam se dizajn sviđa? <span>*</span></label><select id="gift-design" name="odabrani_dizajn" required>{''.join(options)}</select>
           <div id="gift-selected-info" class="gift-choice-message" role="status" aria-live="polite">Dizajn možete izabrati i klikom na karticu u galeriji.</div></div>
          <div class="gift-field"><label for="gift-amount">Vrijednost poklon bona (€) <span>*</span></label><input id="gift-amount" name="vrijednost_eura" type="number" min="1" step="0.01" inputmode="decimal" placeholder="Iznos po vašoj želji" required></div>
          <div class="gift-form-two"><div class="gift-field"><label for="gift-to">Za koga je poklon? <span>*</span></label><input id="gift-to" name="za_koga" maxlength="180" placeholder="Ime ili prigoda" required></div>
           <div class="gift-field"><label for="gift-from">Od koga? <span>*</span></label><input id="gift-from" name="od_koga" maxlength="300" placeholder="Vi, obitelj, prijatelji…" required></div></div>
          <div class="gift-field"><label for="gift-occasion">Prigoda <span class="gift-optional">(neobvezno)</span></label><input id="gift-occasion" name="prigoda" maxlength="160" placeholder="Rođendan, diploma, godišnjica…"></div>
          <div class="gift-field"><label for="gift-message">Osobna poruka <span class="gift-optional">(neobvezno)</span></label><textarea id="gift-message" name="osobna_poruka" rows="3" maxlength="1000" placeholder="Možete napisati svoju posvetu ili nam ostaviti malo prostora za kreativnost."></textarea>
           <label class="gift-check"><input type="checkbox" name="pomoc_oko_poruke" value="Da"><span>Trebam pomoć u osmišljavanju poruke.</span></label></div>
          <div class="gift-form-two"><div class="gift-field"><label for="gift-name">Vaše ime i prezime <span>*</span></label><input id="gift-name" name="ime_narucitelja" autocomplete="name" maxlength="180" required></div>
           <div class="gift-field"><label for="gift-email">Vaša e-mail adresa <span>*</span></label><input id="gift-email" name="email" type="email" autocomplete="email" maxlength="254" required></div></div>
          <div class="gift-field"><label for="gift-note">Još nešto što bismo trebali znati? <span class="gift-optional">(neobvezno)</span></label><textarea id="gift-note" name="napomena" rows="2" maxlength="1000" placeholder="Npr. želite bon s vlastitom fotografijom ili vam treba do određenog datuma."></textarea></div>
          <div class="gift-terms" id="gift-terms"><h4>Važno prije narudžbe</h4><p>Poklon bon vrijedi <strong>12 mjeseci od izdavanja</strong> i može se koristiti za sve usluge agencije Idealab. Vrijednost se koristi jednokratno, za jednu kupnju ili rezervaciju usluge; neiskorištena razlika ne isplaćuje se u novcu. Konačne podatke i uvjete potvrđujemo prije uplate.</p></div>
          <label class="gift-check gift-privacy"><input type="checkbox" required name="privatnost" value="Upoznat/a sam"><span>Upoznat/a sam s <a href="/politika-privatnosti.html" target="_blank" rel="noopener noreferrer">Politikom privatnosti</a> i suglasan/na da me Idealab kontaktira radi ovog upita. <span aria-hidden="true">*</span></span></label>
          <div data-idealab-turnstile class="gift-turnstile" aria-label="Sigurnosna provjera prije slanja"></div>
          <button type="submit" class="gift-submit">Pošaljite svoju ideju <span aria-hidden="true">→</span></button>
          <div id="gift-form-status" class="idealab-form-status" hidden role="status" aria-live="polite"></div>
          <p id="gift-preview-info" class="gift-preview-info" hidden>Na probnoj adresi obrasce ne šaljemo; slanje će biti aktivno na <strong>idealab.hr</strong> nakon objave novog weba. Za sada nam možete pisati na <a href="mailto:info@idealab.hr">info@idealab.hr</a>.</p>
          <p class="gift-form-help">Radije pišete izravno? <a href="mailto:info@idealab.hr?subject=Upit%20za%20poklon%20bon">info@idealab.hr</a></p>
        </form>
      </div>
    </div></section>
    <dialog id="gift-preview" class="gift-dialog" aria-label="Uvećani poklon bon"><form method="dialog"><button type="submit" class="gift-dialog-close" aria-label="Zatvori pregled">×</button></form><img id="gift-preview-image" alt=""><div class="gift-dialog-bottom"><p id="gift-preview-caption"></p><button type="button" id="gift-use-preview" class="gift-primary">Odaberite ovaj dizajn</button></div></dialog>
  </main>'''
    result = page('Poklon bonovi – poklonite putovanje i uspomene', 'Personalizirani poklon bonovi za rođendane, diplome, vjenčanja i obljetnice. Izaberite dizajn, vrijednost i posvetu – Idealab Travel & Tours Rijeka.', '/poklon-bonovi.html', vouchers[4]['image'] if len(vouchers)>4 else vouchers[0]['image'], main)
    result = result.replace('</head>', '<link rel="stylesheet" href="/poklon-bonovi.css?v=1"></head>')
    result = result.replace('</body>', '<script src="/poklon-bonovi.js?v=1" defer></script><script src="/obrasci.js?v=turnstile1" defer></script></body>')
    (out / 'poklon-bonovi.html').write_text(result, encoding='utf-8')

    promo = f'''<section id="poklon-bonovi-najava" class="py-16 bg-white" aria-labelledby="gift-teaser-heading"><div class="container mx-auto px-4"><div class="gift-promo" style="display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:clamp(20px,5vw,60px);align-items:center;max-width:1120px;margin:auto;background:linear-gradient(135deg,#eef4ff,#f8fbff);border-radius:24px;padding:clamp(26px,5vw,55px);overflow:hidden">
      <div><p style="font-size:.78rem;letter-spacing:.12em;font-weight:700;color:#2563eb;margin-bottom:12px">IDEALAB · DARUJTE USPOMENE</p><h2 id="gift-teaser-heading" class="text-3xl md:text-4xl font-bold text-blue-800 mb-5" style="line-height:1.2">Poklonite putovanje.<br>Poklonite uspomene.</h2><p class="text-gray-700 mb-5" style="line-height:1.8">Neki pokloni ostaju u sjećanju mnogo dulje od trenutka kada ih darujemo. Za diplome, rođendane, obljetnice i sve velike životne trenutke.</p><a href="/poklon-bonovi.html" class="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition">Stvorite poseban poklon <span aria-hidden="true">→</span></a></div>
      <a href="/poklon-bonovi.html" aria-label="Pogledajte Idealabove poklon bonove" style="display:block"><img src="{esc(vouchers[4]['image'] if len(vouchers)>4 else vouchers[0]['image'])}" alt="Idealab poklon bon – primjer dizajna" loading="lazy" style="width:100%;height:auto;box-shadow:0 18px 45px rgba(30,64,175,.17);border-radius:12px;transform:rotate(2deg)"></a>
    </div></div></section>
    <style>@media(max-width:700px){{#poklon-bonovi-najava .gift-promo{{grid-template-columns:1fr!important}}}}</style>\n'''
    homepage = out / 'index.html'
    text = homepage.read_text(encoding='utf-8')
    needle = '<!-- Blog Section -->'
    if needle not in text:
        raise ValueError('Ne mogu pronaći sigurno mjesto u index.html za najavu poklon bonova')
    if 'id="poklon-bonovi-najava"' not in text:
        text = text.replace(needle, promo + needle, 1)
    # Keep footer navigation current without changing shared footer source/CMS.
    footer_before = '<li><a href="index.html#blog">Blog i novosti</a></li>'
    footer_after = footer_before + '<li><a href="/poklon-bonovi.html">Poklon bonovi</a></li>'
    if footer_before in text and footer_after not in text:
        text = text.replace(footer_before, footer_after, 1)
    homepage.write_text(text, encoding='utf-8')

    sitemap = out / 'sitemap.xml'
    xml = sitemap.read_text(encoding='utf-8')
    if SITE_URL not in xml:
        xml = xml.replace('</urlset>', '  <url><loc>'+SITE_URL+'</loc></url>\n</urlset>')
    sitemap.write_text(xml, encoding='utf-8')
    print(f'Poklon bonovi: {len(vouchers)} dizajna, nova stranica i najava na naslovnici.')

    # Jedan diskretan pokloncic uz zaglavlje, bez nove stavke izbornika.
    # Dodatak se primjenjuje na izlazne HTML stranice, ne mijenja CMS podatke.
    gift_icon = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
                 'width="19" height="19" fill="none" stroke="currentColor" stroke-width="1.9" '
                 'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
                 '<rect x="3" y="8" width="18" height="13" rx="2"/>'
                 '<path d="M12 8v13M3 12h18M12 8c-1.8 0-5.1-1-5.1-3.2A2.8 2.8 0 0 1 9.6 2C11.2 2 12 5.1 12 8Zm0 0c1.8 0 5.1-1 5.1-3.2A2.8 2.8 0 0 0 14.4 2C12.8 2 12 5.1 12 8Z"/>'
                 '</svg>')
    gift_desktop = ('<a class="idealab-gift-link idealab-gift-link--desktop" '
                    'href="/poklon-bonovi.html" title="Poklon bonovi">'
                    + gift_icon + '<span>Poklon bon</span></a>')
    gift_mobile = ('<a class="idealab-gift-link idealab-gift-link--mobile" '
                   'href="/poklon-bonovi.html" title="Poklon bonovi" aria-label="Poklon bonovi">'
                   + gift_icon + '</a>')
    css_link = '<link rel="stylesheet" href="/idealab-poklon-link.css?v=1">'

    home_file = out / 'index.html'
    homepage = home_file.read_text(encoding='utf-8')
    original_home_header = '<header class="bg-white shadow-md sticky top-0 z-50">'
    if original_home_header not in homepage:
        raise ValueError('Nedostaje ocekivano zaglavlje u index.html: poklon link nije dodan')
    homepage = homepage.replace(original_home_header,
                                '<header class="bg-white shadow-md sticky top-0 z-50 idealab-gift-header">', 1)
    home_cta = '<div class="hidden xl:flex items-center space-x-4">'
    if home_cta not in homepage or '<button id="mobile-menu-button"' not in homepage:
        raise ValueError('Nije pronadjen desktop ili mobilni izbornik na naslovnici')
    homepage = homepage.replace(home_cta, home_cta + gift_desktop, 1)
    homepage = homepage.replace('<button id="mobile-menu-button"',
                                gift_mobile + '<button id="mobile-menu-button"', 1)
    homepage = homepage.replace('</head>', css_link + '\n</head>', 1)
    home_file.write_text(homepage, encoding='utf-8')

    # Zadrzi potpuno isto zaglavlje i na automatski generiranim stranicama
    # putovanja, bloga i poklon bonova. Na njima dodaj i upravljanje hamburgerom.
    match = re.search(r'<header\b[^>]*>.*?</header>', homepage, flags=re.I | re.S)
    if not match:
        raise ValueError('Nedostaje zaglavlje naslovnice')
    shared_header = match.group(0)
    for target, link in [('#', '/'), ('#putovanja', '/#putovanja'),
                         ('#o-nama', '/#o-nama'), ('#blog', '/#blog'),
                         ('#kontakt', '/#kontakt'),
                         ('design-travel.html','/design-travel.html'),
                         ('educational-travel.html','/educational-travel.html')]:
        shared_header = shared_header.replace('href="'+target+'"', 'href="'+link+'"')
    # Vec sucitava postojece pravne/putnicke stranice, ovo je samo mobilni izbornik.
    mobile_js = """<script data-idealab-generated-nav>
    document.addEventListener('DOMContentLoaded',function(){
      const btn=document.getElementById('mobile-menu-button');
      const menu=document.getElementById('mobile-menu');
      if(!btn||!menu)return;
      btn.setAttribute('aria-label','Otvori izbornik');
      btn.setAttribute('aria-expanded','false');
      btn.addEventListener('click',function(){
        const willShow=menu.classList.contains('hidden');
        menu.classList.toggle('hidden');
        btn.setAttribute('aria-expanded',String(willShow));
      });
      menu.querySelectorAll('a').forEach(function(a){
        a.addEventListener('click',function(){
          menu.classList.add('hidden');
          btn.setAttribute('aria-expanded','false');
        });
      });
    });
    </script>"""
    for html_file in out.rglob('*.html'):
        if html_file == home_file:
            continue
        doc = html_file.read_text(encoding='utf-8')
        # Razlicite vrste zaglavlja, bez prekidanja rada drugih obrazaca.
        if '<header class="bg-white shadow-sm">' in doc:
            doc, count = re.subn(r'<header class="bg-white shadow-sm">.*?</header>',
                                 lambda m: shared_header, doc, count=1, flags=re.S)
            if count:
                doc = doc.replace('</body>', mobile_js + '\n</body>', 1)
        elif '<header class="header">' in doc:
            doc = doc.replace('<header class="header">',
                              '<header class="header idealab-gift-header">', 1)
            doc = doc.replace('<a class="button" href="#upit">',
                              gift_desktop + '<a class="button" href="#upit">', 1)
            doc = doc.replace('<button class="menu"',
                              gift_mobile + '<button class="menu"', 1)
        # Nemoj duplicirati CSS niti mijenjati vec generiranu stranicu.
        if '<header' in doc and css_link not in doc:
            doc = doc.replace('</head>', css_link + '\n</head>', 1)
        html_file.write_text(doc, encoding='utf-8')
    print('Poklon link: desktop natpis i mobilni pokloncic dodani u zaglavlje; svi HTML izvori ostaju netaknuti.')
