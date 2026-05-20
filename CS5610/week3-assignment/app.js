// timer + simple cat photo switch
(function () {
    const totalEl = document.getElementById('total');
    const resetBtn = document.getElementById('reset');
    const catImg = document.getElementById('catImg');
  
    // cat photo link
    const photos = [
      '1.jpeg',
      '2.jpg',
      '3.jpeg',
      '4.jpeg',
      '5.jpeg',
      '6.jpeg',
      '7.jpeg',
      '8.jpeg'
    ];
  
    const KEY = 'tw_total_ms';
  
    let totalMs = Number(localStorage.getItem(KEY) || 0);
    let running = true;
    let last = performance.now();
  
    // random start photo
    let idx = Math.floor(Math.random() * photos.length);
    setPhoto(idx);
  
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) running = false;
      else { running = true; last = performance.now(); }
    });
  
    // disabled nav still hover
    document.querySelectorAll('.nav a.disabled').forEach(a => {
      a.addEventListener('click', e => e.preventDefault());
    });
  
    // reset = clear time + change photo
    resetBtn.addEventListener('click', () => {
      if (confirm('Clear total time for this browser?')) {
        totalMs = 0;
        localStorage.setItem(KEY, '0');
        nextPhoto();
        render();
      }
    });
  
    // click image to change photo
    catImg.addEventListener('click', nextPhoto);
    function nextPhoto(){
      idx = (idx + 1) % photos.length;
      setPhoto(idx);
    }
    function setPhoto(i){
      catImg.src = photos[i];
    }
    function tick(now) {
      if (running) {
        const dt = now - last;
        last = now;
        totalMs += dt;
        if ((totalMs | 0) % 1000 < dt) localStorage.setItem(KEY, String(totalMs | 0));
        render();
      }
      requestAnimationFrame(tick);
    }
  
    function render() { totalEl.textContent = toHMS(totalMs | 0); }
  
    function toHMS(ms) {
      const s = (ms / 1000) | 0;
      const h = (s / 3600) | 0;
      const m = ((s % 3600) / 60) | 0;
      const sec = s % 60;
      return [h, m, sec].map(n => String(n).padStart(2, '0')).join(':');
    }
  
    render();
    requestAnimationFrame(t => { last = t; requestAnimationFrame(tick); });
  })();
