/* Idealab: native share when supported; local fallback, no third-party SDKs. */
(()=>{
  'use strict';
  const url=new URL(location.href); url.search=''; url.hash='';
  const address=url.href;
  document.querySelectorAll('[data-idealab-share]').forEach(root=>{
    const toggle=root.querySelector('[data-share-toggle]');
    const panel=root.querySelector('[data-share-panel]');
    const status=root.querySelector('[data-share-status]');
    const field=root.querySelector('[data-share-url]');
    const title=root.dataset.title || document.title;
    const enc=encodeURIComponent;
    root.querySelector('[data-share-facebook]').href='https://www.facebook.com/sharer/sharer.php?u='+enc(address);
    root.querySelector('[data-share-whatsapp]').href='https://wa.me/?text='+enc(title+' '+address);
    root.querySelector('[data-share-email]').href='mailto:?subject='+enc(title)+'&body='+enc(title+'\n'+address);
    field.value=address;
    const show=(open)=>{panel.hidden=!open;toggle.setAttribute('aria-expanded',String(open));};
    toggle.hidden=false;
    show(false);
    toggle.addEventListener('click',async()=>{
      if(!panel.hidden){show(false);return;}
      if(typeof navigator.share==='function'){
        try{await navigator.share({title,url:address});return;}
        catch(err){if(err && err.name==='AbortError')return;}
      }
      show(true);
    });
    root.querySelector('[data-share-copy]').addEventListener('click',async()=>{
      try{await navigator.clipboard.writeText(address);status.textContent='Poveznica je kopirana.';}
      catch(_){field.hidden=false;field.focus();field.select();status.textContent='Označili smo poveznicu. Kopirajte je iz polja.';}
    });
    root.addEventListener('keydown',event=>{if(event.key==='Escape'&&!panel.hidden){show(false);toggle.focus();}});
    document.addEventListener('click',event=>{if(!root.contains(event.target))show(false);});
  });
})();
