#!/usr/bin/env python3
"""Idealab: static pages from existing CMS JSON. No third-party Python packages."""
from pathlib import Path
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlsplit, urlunsplit, quote
import json, re, shutil, unicodedata, datetime

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'dist'
BASE='https://idealab.hr'
BRAND='ideaLAB travel&tours'
CATS={'europa':'Europa','hrvatska':'Hrvatska','advent':'Advent','citybreak':'City break','tematske':'Tematske ture','daleka':'Daleka putovanja'}
FALLBACK='/images/educational_travel_world.jpg'

def s(v): return v.strip() if isinstance(v,str) else ''
def e(v): return escape(s(v),quote=True)
def slug(v):
    v=s(v).lower().replace('đ','d')
    v=''.join(c for c in unicodedata.normalize('NFKD',v) if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+','-',v).strip('-')[:110].rstrip('-')
def url(v, image=False, pdf=False):
    v=s(v)
    if not v or any(ord(c)<32 for c in v) or '\\' in v: return ''
    try: u=urlsplit(v)
    except ValueError: return ''
    if u.scheme:
        if u.scheme not in ('http','https') or not u.netloc or u.username or u.password: return ''
        if image and not re.search(r'\.(jpe?g|png|webp|gif|svg|avif)$',u.path,re.I) and u.hostname!='images.unsplash.com': return ''
    else:
        if u.netloc or v.startswith('//') or '..' in u.path.split('/'): return ''
        if not u.path and u.fragment and not (image or pdf): return '/#'+quote(u.fragment,safe='-._~')
        u=u._replace(path='/'+u.path.lstrip('/'))
        if image and not re.search(r'\.(jpe?g|png|webp|gif|svg|avif)$',u.path,re.I): return ''
    if pdf and not u.path.lower().endswith('.pdf'): return ''
    return urlunsplit(u._replace(path=quote(u.path,safe='/%:@!$&\'()*+,;=-._~'),query=quote(u.query,safe='=&%/?+:;,@-._~'),fragment=quote(u.fragment,safe='-._~%')))
def image(item): return url(item.get('slika'),image=True) or FALLBACK
def absolute(v): return BASE+v if v.startswith('/') else v

def read_json(name):
    data=json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
    if not isinstance(data,list): raise ValueError(name+' mora biti JSON lista')
    return data

def public(data,flag,folder):
    result=[]; used=set()
    for obj in data:
        if not isinstance(obj,dict) or obj.get(flag) is not True or not s(obj.get('naslov')): continue
        item=dict(obj)
        key=slug(item.get('url_naziv') or item['naslov'])
        if not key: raise ValueError('Nedostaje URL naziv: '+item['naslov'])
        if key in used: raise ValueError('Dvostruki URL naziv u '+folder+': '+key+'; upišite različit URL naziv u CMS-u.')
        used.add(key); item['stranica']='/'+folder+'/'+key+'/'
        result.append(item)
    return result

class CleanHTML(HTMLParser):
    allowed=set('p h2 h3 h4 strong b em i u ul ol li br blockquote a img figure figcaption hr'.split())
    blocked=set('script style iframe object embed form input svg math template'.split())
    void={'img','br','hr','input','embed'}
    def __init__(self): super().__init__(convert_charrefs=True); self.parts=[]; self.stack=[]; self.skip=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if self.skip or tag in self.blocked:
            if tag not in self.void: self.stack.append((tag,'',True)); self.skip+=1
            return
        if tag not in self.allowed: return
        extra=''
        if tag=='a':
            href=url(a.get('href'))
            if href: extra=' href="'+e(href)+'"'
        if tag=='img':
            src=url(a.get('src'),image=True)
            if not src:return
            extra=' src="'+e(src)+'" alt="'+e(a.get('alt'))+'" loading="lazy"'
        self.parts.append('<'+tag+extra+'>')
        if tag not in self.void: self.stack.append((tag,tag,False))
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if tag not in self.void:self.handle_endtag(tag)
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag:
                while len(self.stack)>i:
                    _,out,blocked=self.stack.pop()
                    if blocked:self.skip-=1
                    elif out:self.parts.append('</'+out+'>')
                break
    def handle_data(self,data):
        if not self.skip:self.parts.append(escape(data))
    def finish(self):
        self.close()
        while self.stack:
            _,out,blocked=self.stack.pop()
            if out:self.parts.append('</'+out+'>')
        return ''.join(self.parts)
def rich(v):
    if not s(v):return ''
    if not re.search(r'<(?:p|h[234]|ul|ol|div|br|blockquote|img|figure|strong|em)\b',s(v),re.I):
        return ''.join('<p>'+escape(line).replace('\n','<br>')+'</p>' for line in re.split(r'\n\s*\n',s(v)) if line.strip())
    parser=CleanHTML(); parser.feed(s(v)); return parser.finish()
def desc(v):
    v=re.sub(r'\s+',' ',s(v)); return v if len(v)<=160 else v[:157].rsplit(' ',1)[0]+'…'
def date_text(v):
    try:
        d=datetime.date.fromisoformat(s(v)); m='siječnja veljače ožujka travnja svibnja lipnja srpnja kolovoza rujna listopada studenoga prosinca'.split()
        return f'{d.day}. {m[d.month-1]} {d.year}.'
    except ValueError:return ''
def write(path,content):
    p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content,encoding='utf-8')
def write_json(name,data):write(name,json.dumps(data,ensure_ascii=False,indent=2)+'\n')

# Copy original public assets and pages, never modify source CMS data.
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir()
for p in ROOT.iterdir():
    if p.is_file() and (p.suffix.lower() in {'.html','.css','.js','.json','.svg','.png','.jpg','.jpeg','.webp','.gif','.ico','.xml','.txt','.webmanifest','.woff','.woff2','.pdf'} or p.name in {'_headers','_redirects','CNAME'}):
        shutil.copy2(p,OUT/p.name)
    elif p.is_dir() and p.name in {'images','putovanja','dokumenti','assets','fonts','.well-known'}:
        shutil.copytree(p,OUT/p.name,dirs_exist_ok=True)
trips=public(read_json('putovanja.json'),'vidljivo','putovanja')
posts=public(read_json('novosti.json'),'objavljeno','blog')
posts.sort(key=lambda p:s(p.get('datum')),reverse=True)
write_json('putovanja.json',trips);write_json('novosti.json',posts)

# The existing article page supplies the exact current header, footer and typography.
shell=(ROOT/'clanak.html').read_text(encoding='utf-8')
shell=re.sub(r'<script\b[^>]*\bsrc=["\'](?:\./)?clanak\.js[^"\']*["\'][^>]*>\s*</script>','',shell,flags=re.I)
shell=re.sub(r'((?:href|src)=["\'])(?:\./)?((?:index|design-travel|educational-travel|podaci-o-agenciji|uvjeti-putovanja|politika-privatnosti)\.html(?:#[^"\']*)?|footer\.css(?:\?[^"\']*)?)(["\'])',r'\1/\2\3',shell)
shell=re.sub(r'<title>.*?</title>','<!--PAGE_META-->',shell,flags=re.S)
shell=re.sub(r'<meta\s+name=["\']description["\'][^>]*>','',shell,flags=re.I)
shell=re.sub(r'<link\s+rel=["\']canonical["\'][^>]*>','',shell,flags=re.I)
shell=re.sub(r'<meta\s+(?:property|name)=["\'](?:og:|twitter:)[^"\']+["\'][^>]*>','',shell,flags=re.I)

# Consistent typography across all generated articles and itineraries.
shell=shell.replace('</head>', """<style>
.clanak-tekst{overflow-wrap:anywhere;line-height:1.8;}
.clanak-tekst h4{font-size:1.1rem;font-weight:600;color:#1e40af;margin:1.3rem 0 .5rem;line-height:1.4;}
.clanak-tekst figure{margin:1.5rem 0;}.clanak-tekst figcaption{font-size:.85rem;line-height:1.5;color:#6b7280;text-align:center;margin:.5rem 0 1.25rem;}
.clanak-tekst hr{border:0;border-top:1px solid #e5e7eb;margin:1.5rem 0;}
.clanak-tekst img{max-width:100%;height:auto;display:block;}
@media(max-width:640px){.clanak-tekst{font-size:1rem;line-height:1.8;}.clanak-tekst h2{font-size:1.35rem;}.clanak-tekst h3{font-size:1.18rem;}}
.idealab-share [hidden]{display:none!important;}.idealab-share a,.idealab-share button{min-height:44px;}.idealab-share input{min-width:0;max-width:100%;}
</style></head>""")

def share(title,route):
    address=BASE+route
    wa='https://wa.me/?text='+quote(title+' '+address,safe='')
    fb='https://www.facebook.com/sharer/sharer.php?u='+quote(address,safe='')
    mail='mailto:?subject='+quote(title,safe='')+'&body='+quote(title+'\n'+address,safe='')
    return f'''<div class="idealab-share mt-6" data-idealab-share data-title="{e(title)}">
    <button type="button" hidden data-share-toggle aria-expanded="false" aria-controls="idealab-share-panel" class="inline-flex gap-2 items-center border border-blue-700 text-blue-700 rounded-lg px-4 py-2 font-semibold hover:bg-blue-50"><i class="fas fa-share-alt" aria-hidden="true"></i> Podijeli</button>
    <div id="idealab-share-panel" data-share-panel class="mt-3 border border-gray-200 rounded-xl p-4 bg-gray-50">
      <p class="text-sm font-semibold text-blue-900 mb-3">Podijelite ovu stranicu</p>
      <div class="flex flex-wrap gap-2 text-sm">
      <a data-share-whatsapp href="{e(wa)}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-white border border-gray-200 text-gray-700 hover:text-blue-700"><i class="fab fa-whatsapp" aria-hidden="true"></i> WhatsApp</a>
      <a data-share-facebook href="{e(fb)}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-white border border-gray-200 text-gray-700 hover:text-blue-700"><i class="fab fa-facebook-f" aria-hidden="true"></i> Facebook</a>
      <a data-share-email href="{e(mail)}" class="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-white border border-gray-200 text-gray-700 hover:text-blue-700"><i class="far fa-envelope" aria-hidden="true"></i> E-mail</a>
      <button type="button" data-share-copy class="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-white border border-gray-200 text-gray-700 hover:text-blue-700"><i class="fas fa-link" aria-hidden="true"></i> Kopiraj poveznicu</button>
      </div><p class="text-sm text-blue-700 mt-2" role="status" data-share-status></p><input hidden readonly data-share-url aria-label="Poveznica za kopiranje" class="w-full p-2 border rounded text-sm">
    </div></div>'''

def page(title,description,route,img,main,kind='website',date=''):
    full=title+' | '+BRAND; canonical=BASE+route; picture=absolute(img or '/seo-podijeli.jpg')
    tags={'og:type':kind,'og:title':full,'og:description':description,'og:url':canonical,'og:image':picture,'og:site_name':BRAND,'og:locale':'hr_HR'}
    if date:tags['article:published_time']=date
    meta='<title>'+e(full)+'</title>\n<meta name="description" content="'+e(description)+'">\n<link rel="canonical" href="'+e(canonical)+'">\n'
    meta+='\n'.join(f'<meta property="{k}" content="{e(v)}">' for k,v in tags.items())
    meta+='\n<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:title" content="'+e(full)+'">\n<meta name="twitter:description" content="'+e(description)+'">\n<meta name="twitter:image" content="'+e(picture)+'">'
    result=shell.replace('<!--PAGE_META-->',meta)
    result,n=re.subn(r'<main\b[^>]*>.*?</main>',lambda _:main,result,count=1,flags=re.S)
    if n!=1:raise ValueError('clanak.html: nedostaje main')
    if 'data-idealab-share' in main:result=result.replace('</body>','<script src="/dijeljenje.js" defer></script></body>')
    return result

def button(href,label,primary=True):
    cls='bg-blue-600 hover:bg-blue-700 text-white' if primary else 'border border-blue-700 text-blue-700 hover:bg-blue-50'
    return f'<a class="inline-flex justify-center items-center rounded-lg px-5 py-3 font-semibold transition {cls}" href="{e(href)}">{e(label)}</a>'
def section(label,value):
    body=rich(value)
    if not body.strip():return ''
    return '<section class="mt-9 border-t border-gray-200 pt-6"><h2 class="text-2xl font-bold text-blue-800 mb-4">'+e(label)+'</h2><div class="clanak-tekst">'+body+'</div></section>'
def trip_main(t):
    title=s(t['naslov']); pic=image(t); pdf=url(t.get('pdf'),pdf=True)
    category=CATS.get(t.get('kategorija'),'Putovanje'); term=s(t.get('termin')); price=s(t.get('cijena')) or 'Na upit'
    contact='/?putovanje='+quote(title,safe='')+'#kontakt'
    parts=[f'<main class="max-w-5xl mx-auto px-5 py-10 sm:py-14"><a href="/#putovanja" class="inline-block text-blue-700 font-medium mb-6">&larr; Sva putovanja</a><article class="bg-white shadow-md rounded-xl overflow-hidden">',f'<img src="{e(pic)}" alt="{e(title)}" class="w-full h-64 sm:h-96 object-cover">',f'<div class="p-5 sm:p-10"><p class="text-sm font-semibold text-blue-700 mb-3">{e(category)}</p><h1 class="text-3xl sm:text-4xl font-bold text-blue-900 mb-4 leading-tight">{e(title)}</h1>']
    if term: parts.append(f'<p class="inline-block bg-blue-700 text-white rounded px-3 py-1 font-semibold mb-5">{e(term)}</p>')
    if s(t.get('opis')):parts.append(f'<p class="text-lg text-gray-700 leading-relaxed mb-6">{e(t["opis"])}</p>')
    parts.append(f'<div class="bg-blue-50 rounded-xl p-5 flex flex-wrap gap-4 items-center justify-between"><div><p class="text-sm text-gray-600">Cijena</p><p class="text-2xl font-bold text-blue-700">{e(price)}</p></div><div class="flex flex-wrap gap-3">{button(contact,"Pošaljite upit")}')
    if pdf:parts.append(f'<a href="{e(pdf)}" target="_blank" rel="noopener" class="inline-flex justify-center items-center rounded-lg px-5 py-3 font-semibold border border-blue-700 text-blue-700 hover:bg-white">Preuzmite PDF program</a>')
    parts.append('</div></div>'+share(title,t['stranica']))
    for key,label in [('detaljni_opis','O putovanju'),('program','Program putovanja'),('ukljuceno','Što je uključeno u cijenu'),('nije_ukljuceno','Što nije uključeno u cijenu')]:parts.append(section(label,t.get(key)))
    if not pdf and not any(s(t.get(k)) for k in ('detaljni_opis','program','ukljuceno','nije_ukljuceno')):parts.append('<p class="mt-6 text-gray-600">Za detaljnije informacije o programu, dostupnosti i uvjetima putovanja pošaljite nam upit.</p>')
    parts.append('<p class="mt-8 text-sm text-gray-600">Prije prijave provjerite aktualne informacije i ugovorne uvjete. <a class="underline text-blue-700" href="/uvjeti-putovanja.html">Uvjeti putovanja i dokumentacija</a>.</p></div></article></main>')
    return ''.join(parts)
def blog_main(p):
    title=s(p['naslov']); metadata=' • '.join(filter(None,[date_text(p.get('datum')),s(p.get('kategorija'))]))
    return f'<main class="max-w-4xl mx-auto px-5 py-12 sm:py-16"><a href="/index.html#blog" class="inline-block text-blue-700 font-medium mb-8">&larr; Natrag na novosti</a><article class="bg-white shadow-md rounded-xl overflow-hidden p-5 sm:p-10"><p class="text-sm text-gray-500 mb-3">{e(metadata)}</p><h1 class="text-3xl sm:text-4xl font-bold text-blue-900 mb-6 leading-tight">{e(title)}</h1><img class="w-full max-h-[440px] object-cover rounded-xl mb-8" src="{e(image(p))}" alt="{e(title)}"><p class="text-lg text-gray-700 font-medium mb-8">{e(p.get("sazetak"))}</p><div class="clanak-tekst">{rich(p.get("tekst"))}</div>{share(title,p["stranica"])}<div class="mt-10 flex flex-wrap gap-3">{button("/#putovanja","Pogledajte putovanja")}{button("/#blog","Još članaka",False)}</div></article></main>'
for t in trips:write(t['stranica'].strip('/')+'/index.html',page(s(t['naslov']),desc(t.get('opis')) or s(t['naslov']),t['stranica'],image(t),trip_main(t)))
for p in posts:write(p['stranica'].strip('/')+'/index.html',page(s(p['naslov']),desc(p.get('sazetak')) or s(p['naslov']),p['stranica'],image(p),blog_main(p),'article',s(p.get('datum'))))

# Static home cards: crawlers and users see real links even before JavaScript loads.
def card(t,featured=False):
    title=e(t['naslov']); pic=e(image(t)); href=e(t['stranica']); cat=e(CATS.get(t.get('kategorija'),'Putovanje')); term=s(t.get('termin')); date=f'<p class="idealab-trip-date">{e(term)}</p>' if term else ''; price=e(t.get('cijena')) or 'Cijena na upit'; description=e(t.get('opis'))
    if featured:return f'<div class="offer-card bg-white rounded-xl overflow-hidden shadow-lg transition duration-300"><div class="relative"><img src="{pic}" alt="{title}" class="w-full h-64 object-cover" loading="lazy"><div class="absolute top-4 right-4 bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-medium">{cat}</div></div><div class="p-6"><h3 class="text-xl font-bold mb-2">{title}</h3>{date}<p class="text-gray-600 mb-4">{description}</p><div class="flex justify-between items-center"><span class="text-2xl font-bold text-blue-600">{price}</span><a class="text-blue-800 font-medium hover:text-blue-600 flex items-center" href="{href}">Detalji <i class="fas fa-arrow-right ml-2"></i></a></div></div></div>'
    return f'<div class="destination-item bg-white rounded-lg overflow-hidden shadow-md" data-category="{e(t.get("kategorija"))}"><img src="{pic}" alt="{title}" class="w-full h-48 object-cover" loading="lazy"><div class="p-4"><div class="flex justify-between items-start mb-2"><h3 class="text-lg font-bold">{title}</h3><span class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">{cat}</span></div>{date}<p class="text-gray-600 text-sm mb-3">{description}</p><div class="flex justify-between items-center"><span class="text-blue-600 font-bold">{price}</span><a class="text-blue-800 hover:text-blue-600" href="{href}">Detalji <i class="fas fa-arrow-right"></i></a></div></div></div>'
def blog_card(p):
    title=e(p['naslov']); date=e(date_text(p.get('datum'))); cat=e(p.get('kategorija')); metadata=f'<span>{date}</span><span class="mx-2">•</span><span>{cat}</span>'
    return f'<div class="bg-white rounded-lg overflow-hidden shadow-md"><img src="{e(image(p))}" alt="{title}" class="w-full h-48 object-cover" loading="lazy"><div class="p-6"><div class="flex items-center text-sm text-gray-500 mb-2">{metadata}</div><h3 class="text-xl font-bold mb-3">{title}</h3><p class="text-gray-600 mb-4">{e(p.get("sazetak"))}</p><a class="text-blue-800 font-medium hover:text-blue-600 flex items-center" href="{e(p["stranica"])}">Pročitaj više <i class="fas fa-arrow-right ml-2"></i></a></div></div>'
def instagram_link(value):
    link=url(value)
    try:u=urlsplit(link)
    except ValueError:return ''
    if u.scheme!='https' or u.hostname not in ('www.instagram.com','instagram.com'):return ''
    if not re.fullmatch(r'/(?:p|reel|reels)/[A-Za-z0-9_-]+/?',u.path):return ''
    return 'https://www.instagram.com'+u.path.rstrip('/')+'/'

def instagram_section():
    items=read_json('instagram.json') if (ROOT/'instagram.json').exists() else []
    cards=[]
    for item in items:
        if not isinstance(item,dict) or item.get('aktivna') is not True:continue
        title=s(item.get('naslov')); picture=url(item.get('slika'),image=True); href=instagram_link(item.get('poveznica'))
        # Only local images in this gallery; never fetch Instagram embeds or external thumbnails.
        if not title or not picture.startswith('/images/') or not href:continue
        reel=item.get('vrsta')=='reel' or '/reel/' in href or '/reels/' in href
        icon='fas fa-play' if reel else 'fab fa-instagram'; label='Reel' if reel else 'Objava'
        cards.append(f'''<a href="{e(href)}" target="_blank" rel="noopener noreferrer" class="group block bg-white rounded-xl overflow-hidden shadow-md hover:shadow-lg transition focus-visible:ring-2 focus-visible:ring-blue-600" aria-label="{e(title)} – otvori na Instagramu (nova kartica)"><div class="relative overflow-hidden" style="aspect-ratio:4/5"><img src="{e(picture)}" alt="{e(title)}" class="w-full h-full object-cover transition duration-300 group-hover:scale-105" loading="lazy" decoding="async"><span class="absolute top-3 right-3 bg-white text-blue-800 rounded-full w-9 h-9 flex items-center justify-center shadow" aria-hidden="true"><i class="{icon}"></i></span></div><div class="p-3 sm:p-4"><p class="text-xs text-blue-700 mb-1 font-medium">{label}</p><h3 class="font-semibold text-gray-800 text-sm sm:text-base leading-snug">{e(title)}</h3></div></a>''')
        if len(cards)==6:break
    grid='<div class="grid grid-cols-2 md:grid-cols-3 gap-3 sm:gap-6 max-w-5xl mx-auto mb-9">'+''.join(cards)+'</div>' if cards else ''
    return '<section id="instagram" class="py-16 bg-white"><div class="container mx-auto px-4"><div class="text-center mb-9"><p class="text-sm font-semibold tracking-wider text-blue-600 mb-3"><i class="fab fa-instagram mr-2" aria-hidden="true"></i>IDEALAB NA INSTAGRAMU</p><h2 class="text-3xl md:text-4xl font-bold text-blue-800 mb-4">Putovanja kroz naš objektiv</h2><p class="text-gray-600 max-w-2xl mx-auto">Stvarni trenuci, nova otkrića i priče s naših putovanja.</p></div>'+grid+'<div class="text-center"><a class="inline-flex items-center justify-center gap-2 border border-blue-700 text-blue-700 px-6 py-3 rounded-lg font-medium hover:bg-blue-50 transition" href="https://www.instagram.com/idealab.travel.tours/" target="_blank" rel="noopener noreferrer"><i class="fab fa-instagram" aria-hidden="true"></i> Pratite nas na Instagramu</a></div></div></section>\n'

index=(ROOT/'index.html').read_text(encoding='utf-8')
for ident,html in [('featured-grid',''.join(card(t,True) for t in trips if t.get('izdvojeno') is True)),('destinations-grid',''.join(card(t) for t in trips)),('blog-grid',''.join(blog_card(p) for p in posts[:6]))]:
    if ident=='featured-grid':html=''.join(card(t,True) for t in [x for x in trips if x.get('izdvojeno') is True][:3])
    if not html:html='<p class="text-gray-600 col-span-full">Trenutno nema objavljenog sadržaja.</p>'
    pattern=r'(<div\s+id="'+ident+r'"[^>]*>).*?(</div>\s*<template)'
    def replace(m):return m[1].replace('aria-busy="true"','aria-busy="false"')+html+m[2]
    index,n=re.subn(pattern,replace,index,count=1,flags=re.S)
    if n!=1:raise ValueError('index.html: nedostaje '+ident)
index=re.sub(r'<noscript><p class="text-gray-600 mt-4">Za prikaz aktualnog sadržaja omogućite JavaScript.*?</p></noscript>','',index,flags=re.S)
if len(posts)>6:index=index.replace('</template>\n            <div id="blog-more-wrap"','</template>\n            <noscript><a class="text-blue-700 underline" href="/blog/">Pogledaj sve članke</a></noscript>\n            <div id="blog-more-wrap"')
# Prefill an existing contact form, never submit automatically.
index=index.replace('</body>','''<script>(()=>{const t=new URLSearchParams(location.search).get('putovanje');if(!t)return;const m=document.getElementById('message'),s=document.getElementById('subject');if(s)s.value='upit';if(m&&!m.value.trim())m.value='Zanima me putovanje: '+t.slice(0,250)+'\\n';})();</script>\n</body>''')
# Change cache key without changing source page or other script references.
index=re.sub(r'putovanja\.js\?v=[^"\']+','putovanja.js?v=static1',index)
# Insert immediately before the existing newsletter; source remains untouched.
if 'id="instagram"' not in index:
    marker='<!-- Newsletter:'
    if marker in index:index=index.replace(marker,instagram_section()+marker,1)
    else:
        index,n=re.subn(r'<section\b[^>]*\bid=["\']newsletter["\'][^>]*>',lambda m:instagram_section()+m[0],index,count=1)
        if n!=1:raise ValueError('index.html: nedostaje newsletter sekcija')
write('index.html',index)
# Blog index for all posts and discoverability.
listing='<main class="max-w-6xl mx-auto px-5 py-12"><a class="text-blue-700" href="/">&larr; Naslovnica</a><h1 class="text-4xl font-bold text-blue-900 mt-6 mb-8">Blog i novosti</h1><div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">'+''.join(blog_card(p) for p in posts)+'</div></main>'
write('blog/index.html',page('Blog i novosti','Putničke priče, ideje i savjeti turističke agencije Idealab.', '/blog/','/seo-podijeli.jpg',listing))
# Preserve existing article URLs with a browser redirect to the corresponding static page.
legacy=(OUT/'clanak.html').read_text(encoding='utf-8')
legacy=re.sub(r'<meta\s+name="robots"[^>]*>','<meta name="robots" content="noindex,follow">',legacy,flags=re.I)
write('clanak.html',legacy)
legacy_js=OUT/'clanak.js'
if legacy_js.exists():
    old=legacy_js.read_text(encoding='utf-8'); needle='const title=txt(post.naslov);'
    if needle in old:write('clanak.js',old.replace(needle,"if(/^\\/blog\\/[a-z0-9-]+\\/$/.test(txt(post.stranica))){location.replace(post.stranica);return;}\n      "+needle,1))
# Sitemap contains canonical public pages, not drafts, legacy parameter URLs or thank-you page.
urls=['/','/design-travel','/educational-travel','/podaci-o-agenciji','/uvjeti-putovanja','/politika-privatnosti','/blog/']+[x['stranica'] for x in trips+posts]
write('sitemap.xml','<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join('  <url><loc>'+e(BASE+x)+'</loc></url>\n' for x in urls)+'</urlset>\n')
if not (OUT/'404.html').exists():
    notfound=page('Stranica nije pronađena','Ova stranica nije dostupna.','/404.html','/seo-podijeli.jpg','<main class="max-w-3xl mx-auto px-5 py-20 text-center"><h1 class="text-3xl font-bold text-blue-900 mb-4">Stranica nije pronađena</h1><p class="mb-6">Možda je ponuda završila ili je poveznica promijenjena.</p>'+button('/','Povratak na naslovnicu')+'</main>')
    write('404.html',notfound.replace('content="index,follow"','content="noindex,follow"'))
print(f'Idealab: {len(trips)} putovanja, {len(posts)} članaka; izlaz: {OUT.name}')
