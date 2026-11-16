/* ideaLAB: potvrde obrazaca, honeypot i Cloudflare Turnstile. */
(() => {
  'use strict';

  // Site Key is public. The Secret Key stays exclusively in Formspree.
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
    const newsletter = form.dataset.idealabForm === 'newsletter';
    let sending = false;
    let widgetId = null;
    let widgetFailed = false;
    let latestToken = '';

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
      latestToken = '';
      if (widgetId !== null && window.turnstile) {
        try { window.turnstile.reset(widgetId); }
        catch (_) { widgetFailed = true; }
      }
    };

    const mount = () => {
      try {
        if (!window.turnstile || typeof window.turnstile.render !== 'function') {
          throw new Error('Turnstile API is unavailable');
        }
        // Visible verification: users can see if Turnstile is working.
        // The widget still decides if a checkbox is necessary.
        widgetId = window.turnstile.render(container, {
          sitekey: SITE_KEY,
          theme: 'light',
          size: 'flexible',
          appearance: 'always',
          action: newsletter ? 'newsletter' : 'contact',
          callback: (token) => {
            latestToken = token;
            widgetFailed = false;
            // Clear the prior 'verification required' message after success.
            if (status.classList.contains('error') && status.dataset.turnstileError === '1') {
              status.hidden = true;
              status.dataset.turnstileError = '';
            }
          },
          'error-callback': () => { latestToken = ''; widgetFailed = true; },
          'expired-callback': () => { latestToken = ''; },
          'timeout-callback': () => { latestToken = ''; widgetFailed = true; }
        });
        if (widgetId === undefined || widgetId === null) {
          throw new Error('Turnstile widget did not initialize');
        }
      } catch (_) {
        widgetFailed = true;
        widgetId = null;
      }
    };

    widgets.push({ mount, fail: () => { widgetFailed = true; } });

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (sending || !form.reportValidity()) return;
      if (!supportedHost) {
        setStatus('error', 'Probni pregled', 'Slanje sa sigurnosnom provjerom dostupno je na javnoj stranici idealab.hr. Ovdje poruka nije poslana.');
        return;
      }

      let token = latestToken;
      if (widgetId !== null && window.turnstile) {
        try { token = window.turnstile.getResponse(widgetId) || token; }
        catch (_) { widgetFailed = true; }
      }
      if (!token) {
        status.dataset.turnstileError = '1';
        setStatus(
          'error',
          'Potrebna je sigurnosna provjera.',
          widgetFailed || widgetId === null
            ? 'Sigurnosna provjera nije se učitala. Osvježite stranicu i provjerite blokira li je preglednik ili dodatak za privatnost. Možete nam pisati i na info@idealab.hr.'
            : 'Dovršite sigurnosnu provjeru iznad gumba, a zatim ponovno pritisnite Pošalji poruku.'
        );
        return;
      }

      const data = new FormData(form);
      data.set('cf-turnstile-response', token);
      sending = true;
      button.disabled = true;
      button.textContent = 'Slanje…';
      form.setAttribute('aria-busy', 'true');
      status.dataset.turnstileError = '';
      setStatus('pending', 'Šaljemo vašu poruku…', 'Molimo pričekajte trenutak.');

      try {
        const response = await fetch(form.action, {
          method: 'POST',
          body: data,
          headers: { Accept: 'application/json' }
        });
        const result = await response.json().catch(() => null);
        if (response.ok && result && result.ok === true) {
          form.reset();
          setStatus(
            'success',
            newsletter ? 'Hvala na prijavi!' : 'Hvala vam na upitu!',
            newsletter
              ? 'Vaša prijava na newsletter je zaprimljena.'
              : 'Vaša poruka je zaprimljena. Javit ćemo vam se u najkraćem mogućem roku.'
          );
        } else {
          let message = 'Provjerite unesene podatke i pokušajte ponovno. Ako se problem nastavi, javite nam se na info@idealab.hr.';
          if (response.status === 429) {
            message = 'Trenutno je dosegnuto ograničenje slanja. Pokušajte kasnije ili nam se javite na info@idealab.hr.';
          }
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
    const mountAll = () => widgets.forEach((widget) => widget.mount());
    if (window.turnstile && typeof window.turnstile.render === 'function') {
      mountAll();
    } else {
      const script = document.createElement('script');
      script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';
      script.async = true;
      script.onload = () => {
        // The load event fires after the API is available: no second ready()
        // callback is needed, avoiding a fragile extra initialization step.
        if (window.turnstile && typeof window.turnstile.render === 'function') {
          mountAll();
        } else {
          widgets.forEach((widget) => widget.fail());
        }
      };
      script.onerror = () => widgets.forEach((widget) => widget.fail());
      document.head.appendChild(script);
    }
  }
})();
