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
   if(url)img.src=url; else if (!text(raw)) img.src=imgFallback;
   img.loading='lazy';
 }
 function dateAfterTitle(h3,date,isFeatured){
   if(!h3 || !text(date))return;
   // Jedina nova stavka u izvornom izgledu: mali redak datuma ispod naslova.
   const p=document.createElement('p');
   p.className='text-sm text-gray-600 mb-2';
   p.textContent=text(date);
   if(isFeatured)h3.classList.replace('mb-2','mb-1');
   h3.parentElement.insertBefore(p,isFeatured?h3.nextSibling:h3.parentElement.nextSibling);
 }
 function addDate(card,trip,featured){
   const title=$('h3',card);if(!text(trip.termin))return;
   const p=document.createElement('p');p.className='text-sm text-gray-600 mb-2';p.textContent=text(trip.termin);
   if(featured){title.classList.replace('mb-2','mb-1');title.after(p);}
   else{title.parentElement.after(p);}
 }
 function prepareLink(card,trip,featured){
   const a=$('a',card);if(!a)return;
   const pdf=media(trip.pdf,true);
   const i=$('i',a);
   a.textContent=pdf?(featured?'Detalji ':'Program '):'Potraži '; 
   if(i)a.append(i);
   a.href=pdf || '#kontakt';
   if(pdf){a.target='_blank';a.rel='noopener noreferrer';}
   else{
     a.removeAttribute('target');a.removeAttribute('rel');
     a.addEventListener('click',e=>{
       e.preventDefault();
       const subject=$('#subject'),message=$('#message');
       if(subject)subject.value='upit';
       if(message && (!message.value.trim() || /^Zanima me putovanje: [^\n]+\n?$/.test(message.value)))message.value='Zanima me putovanje: '+text(trip.naslov)+'\n';
       const contact=$('#kontakt');if(contact)contact.scrollIntoView({behavior:'smooth'});
     });
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
 const featured=$('.offer-card')?.parentElement;
 const destinations=$('.destination-item')?.parentElement;
 if(featured && destinations){
   const ft=$('.offer-card').cloneNode(true),dt=$('.destination-item').cloneNode(true);
   getJson('putovanja.json').then(all=>{
     if(!Array.isArray(all))throw Error('Popis putovanja nije valjan');
     const trips=all.filter(x=>x && x.vidljivo===true && text(x.naslov));
     featured.replaceChildren(...trips.filter(x=>x.izdvojeno===true).slice(0,3).map(x=>card(x,true,ft)));
     destinations.replaceChildren(...trips.map(x=>card(x,false,dt)));
     const active=$('.filter-btn.active');
     const val=active?.dataset.filter||'all';
     destinations.querySelectorAll('.destination-item').forEach(x=>{x.style.display=val==='all'||x.dataset.category===val?'block':'none';});
   }).catch(e=>console.error('Idealab putovanja: ostaje izvorni prikaz jer podaci nisu učitani.',e));
 }
 const blogGrid=$('#blog .grid');
 if(blogGrid){
   const template=blogGrid.firstElementChild?.cloneNode(true);
   const more=$('#blog .text-center.mt-12 a');
   let blogs=[],shown=3;
   const drawBlog=()=>{
     if(!template)return;
     blogGrid.replaceChildren(...blogs.slice(0,shown).map(x=>{
       const n=template.cloneNode(true);
       changeImage($('img',n),x.slika);
       if($('img',n))$('img',n).alt=text(x.naslov);
       const meta=$('.flex.items-center.text-sm.text-gray-500',n)?.querySelectorAll('span');
       if(meta?.length>=3){
         if(/^\d{4}-\d\d-\d\d$/.test(text(x.datum))){
           const [y,m,d]=x.datum.split('-').map(Number);
           meta[0].textContent=new Intl.DateTimeFormat('hr-HR',{day:'numeric',month:'long',year:'numeric',timeZone:'UTC'}).format(new Date(Date.UTC(y,m-1,d)))+'.';
         }
         meta[2].textContent=text(x.kategorija);
       }
       $('h3',n).textContent=text(x.naslov);
       $('p.text-gray-600',n).textContent=text(x.sazetak);
       const a=$('a',n);if(a)a.href='clanak.html?id='+encodeURIComponent(text(x.id));
       return n;
     }));
     if(more)more.parentElement.hidden=shown>=blogs.length;
   };
   getJson('novosti.json').then(data=>{
     if(!Array.isArray(data))throw Error('Popis bloga nije valjan');
     blogs=data.filter(x=>x && x.objavljeno===true && text(x.naslov) && text(x.id));
     drawBlog();
   }).catch(e=>console.error('Idealab blog: ostaje originalni izgled.',e));
   if(more)more.addEventListener('click',e=>{e.preventDefault();shown+=3;drawBlog();});
 }
 // Rotiraju se samo fotografije koje je vlasnica sama odabrala u CMS-u.
 const hero=$('.hero');
 const motionButton=$('.hero-motion-toggle');
 if(hero && motionButton)motionButton.addEventListener('click',()=>{
   const paused=hero.classList.toggle('motion-paused');
   const label=paused?'Pokreni animaciju pozadine':'Pauziraj animaciju pozadine';
   motionButton.textContent=paused?'▶':'Ⅱ';
   motionButton.setAttribute('aria-pressed',String(paused));
   motionButton.setAttribute('aria-label',label);
   motionButton.title=label;
 });
 if(hero)getJson('pozadine.json').then(items=>{
   if(!Array.isArray(items))return;
   const photos=items.filter(x=>x && x.aktivna===true).map(x=>media(x.slika)).filter(Boolean);
   if(!photos.length)return; // izvorna slika ostaje ako je galerija prazna
   // Svako osvježavanje u istoj kartici prikazuje sljedeću aktivnu fotografiju.
   // Početna je prva aktivna fotografija; pohrana je odvojena za svaki web/putanju.
   const storageKey='idealab.hero.last.v2:'+location.pathname;
   const unique=[...new Set(photos)];
   let previous='';
   try { previous=history.state?.idealabHeroLast||''; } catch(e) {}
   if(!previous)try { previous=sessionStorage.getItem(storageKey)||''; } catch(e) {}
   if(!previous)try { previous=localStorage.getItem(storageKey)||''; } catch(e) {}
   const previousIndex=unique.indexOf(previous);
   const chosen=unique[previousIndex<0?0:(previousIndex+1)%unique.length];
   try { history.replaceState({...history.state,idealabHeroLast:chosen},''); } catch(e) {}
   try { sessionStorage.setItem(storageKey,chosen); } catch(e) {}
   try { localStorage.setItem(storageKey,chosen); } catch(e) {}
   const safe=chosen.replace(/"/g,'%22');
   hero.style.setProperty('--hero-photo', 'url("'+safe+'")');
 }).catch(e=>console.warn('Idealab pozadine: ostaje originalna fotografija.',e));
})();
