(() => {
  let lastSubmitter = null;

  function fetchAndReplace(url, options) {
    if (window.startLoading) {
      window.startLoading();
    }
    fetch(url, options).then(async r => {
      const html = await r.text();
      const finalUrl = r.url;
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      const main = doc.getElementById('content');
      if (!main) { window.location.href = finalUrl; return; }
      document.getElementById('content').innerHTML = main.innerHTML;
      document.title = doc.title;
      window.history.pushState({finalUrl}, '', finalUrl);
      if (window.endLoading) {
        window.endLoading();
      }
      if (window.initUI) {
        window.initUI();
      }
      window.scrollTo(0,0);
    }).catch(() => { window.location.href = url; });
  }

  document.addEventListener('click', e => {
    const btn = e.target.closest('button');
    if (btn && btn.type !== 'button') {
      lastSubmitter = btn;
    }

    const a = e.target.closest('a');
    if (a && a.getAttribute('href') && a.getAttribute('href').startsWith('/') &&
        a.getAttribute('href') !== '/save_as' && a.getAttribute('href') !== '/save-as') {
      e.preventDefault();
      fetchAndReplace(a.href);
    }
  });

  document.addEventListener('submit', e => {
    const form = e.target.closest('form');
    if (!form) {
      return;
    }

    let actionAttr = form.getAttribute('action');
    let path;
    try {
      path = new URL(actionAttr || window.location.href, window.location.href).pathname;
    } catch (error) {
      console.error('Invalid form action URL:', actionAttr, error);
      path = new URL(window.location.href).pathname;
    }

    if (path !== '/save_as' && path !== '/save-as') {
      e.preventDefault();
      const method = (form.method || 'GET').toUpperCase();
      let url = actionAttr || window.location.href;
      const opts = { method, credentials: 'same-origin' };
      const data = new FormData(form);
      const submitter = e.submitter || lastSubmitter;
      if (submitter && submitter.name) {
        data.append(submitter.name, submitter.value);
      }
      lastSubmitter = null;
      if (method === 'GET') {
        const params = new URLSearchParams(data);
        url += (url.includes('?') ? '&' : '?') + params.toString();
      } else {
        opts.body = data;
      }
      fetchAndReplace(url, opts);
    }
  });

  window.addEventListener('popstate', e => {
    if (e.state && e.state.url) {
      fetchAndReplace(e.state.url);
    }
  });
})();
