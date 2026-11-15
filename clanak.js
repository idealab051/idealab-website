/* Idealab – javna stranica pojedinog članka. */
(() => {
  'use strict';
  const root = document.getElementById('clanak-sadrzaj');
  const wanted = new URLSearchParams(window.location.search).get('id') || '';
  const txt = value => typeof value === 'string' ? value.trim() : '';
  const node = (tag, css, text) => {
    const n=document.createElement(tag);
    if(css) n.className=css;
    if(text !== undefined) n.textContent=text;
    return n;
  };
  const safeUrl = input => {
    try { const u=new URL(input.startsWith('/') && !input.startsWith('//') ? input.slice(1) : input,document.baseURI);return /^https?:$/.test(u.protocol)?u.href:''; }
    catch (_){return '';}
  };
  function dateText(d){
    if (!/^\d{4}-\d\d-\d\d/.test(txt(d))) return '';
    const [y,m,day]=d.slice(0,10).split('-').map(Number);
    return new Intl.DateTimeFormat('hr-HR',{day:'numeric',month:'long',year:'numeric',timeZone:'UTC'}).format(new Date(Date.UTC(y,m-1,day)));
  }
  // Render formatted HTML safely: ignore scripts, handlers, styles, embedded frames.
  function safeArticle(html){
    const doc=new DOMParser().parseFromString(txt(html),'text/html');
    const good=new Set(['P','H2','H3','H4','STRONG','B','EM','I','U','UL','OL','LI','BR','BLOCKQUOTE','A','IMG','FIGURE','FIGCAPTION','HR']);
    const forbidden=new Set(['SCRIPT','STYLE','IFRAME','OBJECT','EMBED','FORM','INPUT','SVG','MATH','TEMPLATE']);
    function build(from,to){
      for(const child of from.childNodes){
        if(child.nodeType===Node.TEXT_NODE){to.append(document.createTextNode(child.textContent));continue;}
        if(child.nodeType!==Node.ELEMENT_NODE || forbidden.has(child.tagName))continue;
        if(!good.has(child.tagName)){build(child,to);continue;}
        const tag=child.tagName.toLowerCase();
        if(tag==='img'){
          const url=safeUrl(child.getAttribute('src') || '');
          if(!url || !/\.(png|jpe?g|webp|gif)$/i.test(new URL(url).pathname))continue;
          const image=document.createElement('img');image.src=url;image.alt=child.getAttribute('alt')||'';image.loading='lazy';to.append(image);continue;
        }
        const clean=document.createElement(tag);
        if(tag==='a'){
          const href=safeUrl(child.getAttribute('href')||'');
          if(href){clean.href=href;clean.rel='noopener noreferrer';clean.target='_blank';}
        }
        build(child,clean);to.append(clean);
      }
    }
    const fragment=document.createDocumentFragment();
    build(doc.body,fragment);
    return fragment;
  }
  function showUnavailable(){root.replaceChildren(node('h1','text-2xl font-bold text-blue-800 mb-4','Članak nije dostupan'),node('p','text-gray-600','Možda je uklonjen ili još nije objavljen.'));document.title='Članak nije dostupan | ideaLAB';}
  if(!wanted){showUnavailable();return;}
  fetch('./novosti.json',{cache:'no-store'})
    .then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json();})
    .then(data=>{
      if(!Array.isArray(data))throw Error('Neispravni podaci');
      const post=data.find(x=>x && x.objavljeno===true && txt(x.id)===wanted);
      if(!post){showUnavailable();return;}
      const title=txt(post.naslov);
      document.title=title+' | ideaLAB travel&tours';
      const wrap=document.createDocumentFragment();
      const meta=node('p','text-sm text-gray-500 mb-3',[dateText(post.datum),txt(post.kategorija)].filter(Boolean).join(' • '));wrap.append(meta);
      wrap.append(node('h1','text-3xl sm:text-4xl font-bold text-blue-900 mb-6 leading-tight',title));
      const hero=safeUrl(txt(post.slika));
      if(hero && (/\.(png|jpe?g|webp|gif)$/i.test(new URL(hero).pathname) || new URL(hero).hostname==='images.unsplash.com')){
        const image=node('img','w-full max-h-[440px] object-cover rounded-xl mb-8');image.src=hero;image.alt=title;wrap.append(image);
      }
      if(txt(post.sazetak))wrap.append(node('p','text-lg text-gray-700 font-medium mb-8',txt(post.sazetak)));
      const body=node('div','clanak-tekst');body.append(safeArticle(post.tekst));wrap.append(body);root.replaceChildren(wrap);
      const desc=document.querySelector('meta[name="description"]');if(desc)desc.content=txt(post.sazetak).slice(0,160);
    })
    .catch(err=>{console.error('Idealab blog:',err);showUnavailable();});
})();
