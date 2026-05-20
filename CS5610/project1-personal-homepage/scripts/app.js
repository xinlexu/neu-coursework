document.addEventListener('DOMContentLoaded', () => {
    const y = document.getElementById('year');
    if (y) y.textContent = new Date().getFullYear();
  });
  
  (function theme() {
    const btn = document.getElementById('theme');
    if (!btn) return;
    const key = 'xx_theme';
    function apply(mode) {
      if (mode === 'system') { document.documentElement.removeAttribute('data-theme'); return; }
      if (mode === 'light') { document.documentElement.setAttribute('data-theme', 'light'); return; }
      document.documentElement.setAttribute('data-theme', 'dark');
    }
    let mode = localStorage.getItem(key) || 'system';
    apply(mode);
    btn.addEventListener('click', () => {
      mode = mode === 'system' ? 'light' : mode === 'light' ? 'dark' : 'system';
      localStorage.setItem(key, mode);
      apply(mode);
    });
  })();
  
  (async function loadLinks() {
    const box = document.getElementById('links');
    const status = document.getElementById('links-status');
    if (!box) return;
    try {
      const res = await fetch('/api/links', { headers: { 'Accept': 'application/json' } });
      if (!res.ok) throw new Error(String(res.status));
      const data = await res.json();
      if (!Array.isArray(data) || data.length === 0) {
        box.innerHTML = '<p class="muted">No links yet.</p>';
        return;
      }
      box.innerHTML = data.map(l => `
        <a class="card link-card" href="${l.url}" target="_blank" rel="noopener">
          <div class="link-title">${l.title}</div>
          <div class="muted">${l.category}</div>
        </a>
      `).join('');
      if (status) status.textContent = '';
    } catch (e) {
      if (status) status.textContent = 'Failed to load links.';
    }
  })();
  
  (function galleryLightbox() {
    const grid = document.getElementById('gallery');
    if (!grid) return;
  
    const btns = Array.from(grid.querySelectorAll('.img-btn'));
    const lb = document.getElementById('lightbox');
    const lbImg = document.getElementById('lightbox-img');
    const prev = document.getElementById('prev');
    const next = document.getElementById('next');
    const close = document.getElementById('lightbox-close');
  
    let idx = -1;
  
    function show(src) {
      lbImg.style.opacity = '0';
      lbImg.style.transform = 'scale(0.985)';
      lbImg.onload = () => {
        requestAnimationFrame(() => {
          lbImg.style.opacity = '1';
          lbImg.style.transform = 'scale(1)';
        });
      };
      lbImg.src = src;
    }
  
    const open = i => {
      idx = i;
      lb.classList.remove('is-hiding');
      lb.removeAttribute('hidden');
      show(btns[idx].dataset.full);
    };
  
    const hide = () => {
      lb.classList.add('is-hiding');
      const end = () => {
        lb.setAttribute('hidden','');
        lb.classList.remove('is-hiding');
        lbImg.removeAttribute('src');
        lb.removeEventListener('transitionend', end);
        idx = -1;
      };
      lb.addEventListener('transitionend', end, { once: true });
    };
  
    const move = d => {
      if (idx < 0) return;
      idx = (idx + d + btns.length) % btns.length;
      show(btns[idx].dataset.full);
    };
  
    if (lb && !lb.hasAttribute('hidden')) hide();
    btns.forEach((b,i)=> b.addEventListener('click', () => open(i)));
    prev && prev.addEventListener('click', () => move(-1));
    next && next.addEventListener('click', () => move(1));
    close && close.addEventListener('click', hide);
    document.addEventListener('keydown', (e) => {
      if (lb.hasAttribute('hidden')) return;
      if (e.key === 'Escape') hide();
      if (e.key === 'ArrowLeft') move(-1);
      if (e.key === 'ArrowRight') move(1);
    });
  })();
  
  (function guestbook() {
    const form = document.getElementById('gb-form');
    const list = document.getElementById('gb-list');
    const status = document.getElementById('gb-status');
    if (!form || !list) return;
  
    function fmt(ts) { return new Date(ts).toLocaleString(); }
  
    function render(items) {
      list.innerHTML = '';
      if (!Array.isArray(items) || items.length === 0) {
        list.innerHTML = '<p class="muted">No messages yet.</p>';
        return;
      }
      for (const it of items) {
        const card = document.createElement('div');
        card.className = 'gb-item';
        const head = document.createElement('div');
        head.className = 'gb-head';
        const who = document.createElement('div');
        who.textContent = it.nickname;
        const when = document.createElement('time');
        when.dateTime = it.created_at;
        when.textContent = fmt(it.created_at);
        head.appendChild(who);
        head.appendChild(when);
        const msg = document.createElement('p');
        msg.textContent = it.message;
        card.appendChild(head);
        card.appendChild(msg);
        list.appendChild(card);
      }
    }
  
    async function load() {
      status.textContent = 'Loading…';
      try {
        const res = await fetch('/api/guestbook');
        if (!res.ok) throw new Error('bad');
        const data = await res.json();
        render(data);
        status.textContent = '';
      } catch {
        status.textContent = 'Failed to load.';
      }
    }
  
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      const nickname = String(fd.get('nickname') || '').trim();
      const message = String(fd.get('message') || '').trim();
      if (!nickname || !message) { status.textContent = 'Please fill nickname and message.'; return; }
      if (message.length > 140) { status.textContent = 'Message must be 140 characters or less.'; return; }
  
      try {
        status.textContent = 'Submitting…';
        const res = await fetch('/api/guestbook', {
          method: 'POST',
          headers: { 'Content-Type':'application/json' },
          body: JSON.stringify({ nickname, message })
        });
        if (!res.ok) throw new Error('bad');
        form.reset();
        await load();
      } catch {
        status.textContent = 'Submit failed.';
      }
    });
  
    load();
  })();
  