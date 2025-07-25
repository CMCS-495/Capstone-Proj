(() => {
  function fetchAndReplace(url, options) {
    if (window.startLoading) window.startLoading();
    fetch(url, options).then(r => r.text()).then(html => {
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      const main = doc.getElementById('content');
      if (!main) { window.location.href = url; return; }
      document.getElementById('content').innerHTML = main.innerHTML;
      document.title = doc.title;
      window.history.pushState({url}, '', url);
      if (window.endLoading) window.endLoading();
      if (window.initUI) window.initUI();
      window.scrollTo(0,0);
    }).catch(() => { window.location.href = url; });
  }

  document.addEventListener('click', e => {
    const a = e.target.closest('a');
    if (a && a.getAttribute('href') && a.getAttribute('href').startsWith('/') &&
        a.getAttribute('href') !== '/save_as' && a.getAttribute('href') !== '/save-as') {
      e.preventDefault();
      fetchAndReplace(a.href);
    }
  });

  document.addEventListener('submit', e => {
    const form = e.target.closest('form');
    if (!form) return;
    const path = new URL(form.action, window.location.href).pathname;
    if (path !== '/save_as' && path !== '/save-as') {
      e.preventDefault();
      const data = new FormData(form);
      fetchAndReplace(form.action, { method: form.method || 'GET', body: data });
    }
  });

  window.addEventListener('popstate', e => {
    if (e.state && e.state.url) {
      fetchAndReplace(e.state.url);
    }
  });
})();
