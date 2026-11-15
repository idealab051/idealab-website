/* ideaLAB: hrvatske potvrde, honeypot i Cloudflare Turnstile. */
(() => {
  'use strict';
  const SITE_KEY = '0x4AAAAAAGClY7aG2fUC0R3K';
  const supportedHost = location.protocol === 'https:' &&
    (location.hostname === 'idealab.hr' || location.hostname === 'www.idealab.hr');
  const widgets = [];
  document.querySelectorAll('form[data-idealab-form]').forEach((form) => {
    const button = form.querySelector('button[type="submit"], input[type="submit"]');
    const status = document.getElementById(form.dataset.status);
    const container = form.querySelector('[data-idealab-turnstile]');
    if (!button || !status || !container) return;
    const originalLabel = button.textContent;
    let sending = false;
    let widgetId = null;
    let widgetFailed = false;
    const newsletter = form.dataset.idealabForm === 'newsletter';
    const setStatus = (kind, title, message) => {
      status.hidden = false;
      status.className = 'idealab-form-status ' + kind;
      status.replaceChildren();
      const heading = document.createElement('strong');
      heading.textContent = title;
      const detail = document.createElement('p');
      detail.textContent = message;
      status.append(heading, detail);
    };
    const resetWidget = () => {
      if (widgetId !== null && window.turnstile) {
        try { window.turnstile.reset(widgetId); } catch (_) { widgetFailed = true; }
      }
    };
    widgets.push({ mount() {
      try {
        widgetId = window.turnstile.render(container, {
          sitekey: SITE_KEY,
          theme: 'light',
          size: 'flexible',
          appearance: 'interaction-only',
          action: newsletter ? 'newsletter' : 'contact',
          callback: () => { widgetFailed = false; },
          'error-callback': () => { widgetFailed = true; },
          'expired-callback': () => { widgetFailed = false; },
          'timeout-callback': () => { widgetFailed = true; }
        });
      } catch (_) { widgetFailed = true; }
    }, fail() { widgetFailed = true; } });
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (sending || !form.reportValidity()) return;
      if (!supportedHost) {
        setStatus('error', 'Probni pregled', 'Slanje sa sigurnosnom provjerom dostupno je na javnoj stranici idealab.hr. Ovdje poruka nije poslana.');
        return;
      }
      let token = '';
      try { if (widgetId !== null && window.turnstile) token = window.turnstile.getResponse(widgetId) || ''; } catch (_) { widgetFailed = true; }
      if (!token) {
        setStatus('error', 'Potrebna je sigurnosna provjera.', widgetFailed ? 'Osvježite stranicu ili omogućite sigurnosnu provjeru u pregledniku. Možete nam se javiti i na info@idealab.hr.' : 'Pričekajte da se sigurnosna provjera dovrši ili potvrdite prikazanu provjeru, zatim ponovno pritisnite gumb za slanje.');
        return;
      }
      const data = new FormData(form);
      data.set('cf-turnstile-response', token);
      sending = true;
      button.disabled = true;
      button.textContent = 'Slanje…';
      form.setAttribute('aria-busy', 'true');
      setStatus('pending', 'Šaljemo vašu poruku…', 'Molimo pričekajte trenutak.');
      try {
        const response = await fetch(form.action, { method: 'POST', body: data, headers: { Accept: 'application/json' } });
        const result = await response.json().catch(() => null);
        if (response.ok && result && result.ok === true) {
          form.reset();
          setStatus('success', newsletter ? 'Hvala na prijavi!' : 'Hvala vam na upitu!', newsletter ? 'Vaša prijava na newsletter je zaprimljena.' : 'Vaša poruka je zaprimljena. Javit ćemo vam se u najkraćem mogućem roku.');
        } else {
          let message = 'Provjerite unesene podatke i pokušajte ponovno. Ako se problem nastavi, javite nam se na info@idealab.hr.';
          if (response.status === 429) message = 'Trenutno je dosegnuto ograničenje slanja. Pokušajte kasnije ili nam se javite na info@idealab.hr.';
          setStatus('error', 'Slanje nije potvrđeno.', message);
        }
      } catch (_) {
        setStatus('error', 'Slanje nije potvrđeno.', 'Provjerite internetsku vezu. Ako niste sigurni je li poruka zaprimljena, kontaktirajte nas na info@idealab.hr.');
      } finally {
        resetWidget();
        sending = false;
        button.disabled = false;
        button.textContent = originalLabel;
        form.removeAttribute('aria-busy');
      }
    });
  });
  if (supportedHost && widgets.length) {
    const script = document.createElement('script');
    script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';
    script.async = true;
    script.onload = () => {
      if (window.turnstile && typeof window.turnstile.ready === 'function') {
        window.turnstile.ready(() => widgets.forEach(widget => widget.mount()));
      } else widgets.forEach(widget => widget.fail());
    };
    script.onerror = () => widgets.forEach(widget => widget.fail());
    document.head.appendChild(script);
  }
})();
