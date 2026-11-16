/* Idealab – samo podatkovno povezivanje postojećih, ORIGINALNIH kartica.
   Izvorni izgled, Tailwind klase, Poppins i raspored ostaju iz originala. */
(() => {
 'use strict';
 const $ = (s,root=document) => root.querySelector(s);
 const text = x => typeof x === 'string' ? x.trim() : '';
 const catLabel = {europa:'Europa',hrvatska:'Hrvatska',advent:'Advent',citybreak:'City break',tematske:'Tematske ture',daleka:'Daleka putovanja'};
 const cats = Object.keys(catLabel);
 const imgFallback = 'images/educational_travel_world.jpg';
 function media(raw,allowPdf=false){
   const v=text(raw);if(!v)return '';
   try {
     const u=new URL(v.startsWith('/') && !v.startsWith('//') ? v.slice(1) : v, document.baseURI);
     if(!['https:','http:'].includes(u.protocol))return '';
     if(allowPdf && !/\.pdf$/i.test(u.pathname))return '';
     if(!allowPdf && !/\.(jpg|jpeg|png|webp|gif)$/i.test(u.pathname) && u.hostname!=='images.unsplash.com')return '';
     return u.href;
   }catch{return '';}
 }
 function getJson(path){return fetch(path,{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json();});}
 function changeImage(img,raw){
   if(!img)return;
   const url=media(raw);
   img.src=url || imgFallback;
   img.loading='lazy';
 }
 function addDate(card,trip,featured){
   const title=$('h3',card);if(!title || !text(trip.termin))return;
   const p=document.createElement('p');p.className='idealab-trip-date';p.textContent=text(trip.termin);
   if(featured){title.classList.replace('mb-2','mb-1');title.after(p);}
   else{title.parentElement.after(p);}
 }
 function prepareLink(card,trip,featured){
   const a=$('a',card);if(!a)return;
   const i=$('i',a);
   const page=text(trip.stranica);
   const pdf=media(trip.pdf,true);
   if(/^\/putovanja\/[a-z0-9-]+\/$/.test(page)){
     a.textContent='Detalji '; if(i)a.append(i); a.href=page;
     a.removeAttribute('target');a.removeAttribute('rel');
   }else{
     a.textContent=pdf?'Program ':'Potraži ';if(i)a.append(i);a.href=pdf||'#kontakt';
     if(pdf){a.target='_blank';a.rel='noopener noreferrer';}
     else{a.removeAttribute('target');a.removeAttribute('rel');a.addEventListener('click',()=>{
       const subject=$('#subject'),message=$('#message');if(subject)subject.value='upit';
       if(message&&!message.value.trim())message.value='Zanima me putovanje: '+text(trip.naslov)+'\n';
     });}
   }
 }
 function card(t,featured,template){
   const n=template.cloneNode(true);
   n.style.display='';
   const title=$('h3',n);if(title)title.textContent=text(t.naslov);
   changeImage($('img',n),t.slika);
   if($('img',n))$('img',n).alt=text(t.naslov);
   if(featured){
     const badge=$('.relative .absolute',n);if(badge)badge.textContent=catLabel[t.kategorija]||'Putovanje';
   }else{
     n.dataset.category=text(t.kategorija);
     n.classList.remove(...cats);
     if(cats.includes(t.kategorija))n.classList.add(t.kategorija);
     const badge=$('span.bg-blue-100',n);if(badge)badge.textContent=catLabel[t.kategorija]||'Putovanje';
   }
   const body=$('p.text-gray-600',n);
   if(body)body.textContent=text(t.opis);
   addDate(n,t,featured);
   const price=featured?$('span.text-2xl',n):$('span.text-blue-600.font-bold',n);
   if(price)price.textContent=text(t.cijena)||'Cijena na upit';
   prepareLink(n,t,featured);
   return n;
 }
 const featured=$('#featured-grid');
 const destinations=$('#destinations-grid');
 const status=(grid,msg)=>{const p=document.createElement('p');p.className='text-gray-600 col-span-full';p.setAttribute('role','status');p.textContent=msg;grid.replaceChildren(p);grid.setAttribute('aria-busy','false');};
 const templateFor=id=>document.getElementById(id)?.content.firstElementChild;
 if(featured && destinations){
   const ft=templateFor('offer-card-template'),dt=templateFor('destination-card-template');
   getJson('putovanja.json').then(all=>{
     if(!Array.isArray(all))throw Error('Popis putovanja nije valjan');
     const trips=all.filter(x=>x && x.vidljivo===true && text(x.naslov));
     if(!ft || !dt)throw Error('Nedostaje predložak');
     const selected=trips.filter(x=>x.izdvojeno===true).slice(0,3);
     if(selected.length) featured.replaceChildren(...selected.map(x=>card(x,true,ft))); else status(featured,'Trenutno nema izdvojenih putovanja.');
     if(trips.length) destinations.replaceChildren(...trips.map(x=>card(x,false,dt))); else status(destinations,'Trenutno nema objavljenih putovanja. Javite nam se za ponudu.');
     featured.setAttribute('aria-busy','false');destinations.setAttribute('aria-busy','false');
     const active=$('.filter-btn.active');
     const val=active?.dataset.filter||'all';
     destinations.querySelectorAll('.destination-item').forEach(x=>{x.style.display=val==='all'||x.dataset.category===val?'block':'none';});
   }).catch(e=>{console.error('Idealab putovanja:',e); const msg='Aktualna putovanja trenutno nisu dostupna. Osvježite stranicu ili nam se javite na info@idealab.hr.';if(!featured.querySelector('.offer-card'))status(featured,msg);if(!destinations.querySelector('.destination-item'))status(destinations,msg);});
 }
 const blogGrid=$('#blog-grid');
 if(blogGrid){
   const template=templateFor('blog-card-template');
   const more=$('#blog-more');
   const moreWrap=$('#blog-more-wrap');
   const limit=6;
   let blogs=[],expanded=false;
   const dateKey=x=>{
     const value=text(x.datum);
     if(!/^\d{4}-\d{2}-\d{2}$/.test(value))return -Infinity;
     const time=Date.parse(value+'T00:00:00Z');
     return Number.isFinite(time) && new Date(time).toISOString().slice(0,10)===value ? time : -Infinity;
   };
   const syncMore=()=>{
     if(moreWrap)moreWrap.hidden=blogs.length<=limit;
     if(more){more.textContent=expanded?'Prikaži manje':'Pogledaj sve članke';more.setAttribute('aria-expanded',String(expanded));}
   };
   const drawBlog=()=>{
     if(!template){status(blogGrid,'Članci trenutno nisu dostupni.');if(moreWrap)moreWrap.hidden=true;return;}
     if(!blogs.length){status(blogGrid,'Trenutno nema objavljenih članaka.');syncMore();return;}
     blogGrid.replaceChildren(...blogs.slice(0,expanded?blogs.length:limit).map(x=>{
       const n=template.cloneNode(true);
       changeImage($('img',n),x.slika);
       if($('img',n))$('img',n).alt=text(x.naslov);
       const meta=$('.flex.items-center.text-sm.text-gray-500',n)?.querySelectorAll('span');
       if(meta?.length>=3){
         const time=dateKey(x);
         if(Number.isFinite(time)){
           meta[0].textContent=new Intl.DateTimeFormat('hr-HR',{day:'numeric',month:'long',year:'numeric',timeZone:'UTC'}).format(new Date(time)).replace(/\.$/,'')+'.';
         }else{meta[0].hidden=true;}
         meta[2].textContent=text(x.kategorija);
         meta[2].hidden=!meta[2].textContent;
         meta[1].hidden=meta[0].hidden||meta[2].hidden;
       }
       $('h3',n).textContent=text(x.naslov);
       $('p.text-gray-600',n).textContent=text(x.sazetak);
       const a=$('a',n);if(a){const page=text(x.stranica);a.href=/^\/blog\/[a-z0-9-]+\/$/.test(page)?page:'clanak.html?id='+encodeURIComponent(text(x.id));}
       return n;
     }));
     blogGrid.setAttribute('aria-busy','false');
     syncMore();
   };
   getJson('novosti.json').then(data=>{
     if(!Array.isArray(data))throw Error('Popis bloga nije valjan');
     blogs=data.filter(x=>x && x.objavljeno===true && text(x.naslov) && text(x.id))
       .sort((a,b)=>{const da=dateKey(a),db=dateKey(b);return da===db?0:da>db?-1:1;});
     drawBlog();
   }).catch(e=>{console.error('Idealab blog:',e);if(!blogGrid.querySelector('h3'))status(blogGrid,'Članci trenutno nisu dostupni. Osvježite stranicu.');if(moreWrap)moreWrap.hidden=true;});
   if(more)more.addEventListener('click',()=>{expanded=!expanded;drawBlog();});
 }
})();
