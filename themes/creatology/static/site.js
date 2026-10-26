(() => {
  const font = document.createElement('link');
  font.rel = 'stylesheet';
  font.href = 'https://fonts.googleapis.com/css2?family=Cairo:wght@600;700&family=IBM+Plex+Sans+Arabic:wght@400;600&family=Inter:wght@400;600&display=swap';
  document.head.appendChild(font);

  const local = ['localhost','127.0.0.1'].includes(location.hostname);
  const localURL = value => { try { const u = new URL(value, location.href); if (u.hostname === 'draymanamer.com') return location.origin + u.pathname + u.search + u.hash; } catch {} return value; };
  if (local) {
    document.querySelectorAll('img[src],iframe[src],video[src],source[src]').forEach(el => el.src = localURL(el.getAttribute('src')));
    document.querySelectorAll('[srcset]').forEach(el => el.setAttribute('srcset',el.getAttribute('srcset').replaceAll('https://draymanamer.com',location.origin)));
    document.addEventListener('click',e => { const a=e.target.closest('a[href]'); if(a && !e.ctrlKey && !e.metaKey && !a.hasAttribute('download') && a.target !== '_blank'){ const u=localURL(a.href); if(u!==a.href){e.preventDefault();location.assign(u);} } });
  }
  const menu=document.querySelector('.menu-toggle');menu?.addEventListener('click',()=>{const open=menu.getAttribute('aria-expanded')!=='true';menu.setAttribute('aria-expanded',String(open));document.querySelector('.site-header').classList.toggle('menu-open',open);});
  document.querySelectorAll('.submenu-toggle').forEach(b=>b.addEventListener('click',()=>{const open=b.getAttribute('aria-expanded')!=='true';b.setAttribute('aria-expanded',String(open));b.parentElement.classList.toggle('is-open',open);}));
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){if(dialog&&dialog.open)dialog.close();document.querySelector('.site-header')?.classList.remove('menu-open');menu?.setAttribute('aria-expanded','false');document.querySelectorAll('.is-open').forEach(n=>n.classList.remove('is-open'));document.querySelectorAll('.submenu-toggle').forEach(n=>n.setAttribute('aria-expanded','false'));}});
  const dialog=document.querySelector('#search-dialog');let index;
  const normalize=s=>s.toLowerCase().normalize('NFKD').replace(/[\u064b-\u065f\u0670]/g,'').replace(/[أإآ]/g,'ا').replace(/ى/g,'ي');
  const search=async q=>{ index ||= await fetch('/search-data.json').then(r=>r.json()); const results=q.trim()?index.filter(i=>normalize(i.title+' '+i.text).includes(normalize(q))).slice(0,40):[];const list=document.querySelector('#search-results');list.replaceChildren();results.forEach(i=>{const li=document.createElement('li'),a=document.createElement('a');a.href=local?localURL(i.url):i.url;a.textContent=i.title;li.append(a);list.append(li);});document.querySelector('.search-status').textContent=q?`${results.length} نتيجة`:'';};
  document.querySelector('.search-toggle')?.addEventListener('click',()=>{dialog.showModal();document.querySelector('#site-search').focus();});
  document.querySelector('#site-search')?.addEventListener('input',e=>search(e.target.value).catch(()=>{document.querySelector('.search-status').textContent='تعذر تحميل البحث';}));
  const query=new URLSearchParams(location.search).get('s');if(query){dialog.showModal();document.querySelector('#site-search').value=query;search(query);}
  const holder=document.querySelector('.contact-form'),form=holder?.querySelector('form');
  if(form){form.removeAttribute('novalidate');form.querySelectorAll('[aria-required=true]').forEach(i=>i.required=true);form.addEventListener('submit',async e=>{e.preventDefault();if(!form.reportValidity())return;const status=holder.querySelector('.form-status'),button=form.querySelector('[type=submit]');button.disabled=true;status.textContent='Sending…';try{const r=await fetch(local?'/api/contact':holder.dataset.endpoint,{method:'POST',body:new FormData(form)});const data=await r.json();status.textContent=data.message||'Unable to send. Please try again.';if(data.status==='mail_sent')form.reset();if(!r.ok)status.textContent=data.message||'Unable to send. Please try again.';}catch{status.textContent='Unable to send. Please try again.';}finally{button.disabled=false;}});}
  document.querySelectorAll(".prose p, .prose td").forEach(el => { if (el.children.length === 0 && el.textContent.includes("http")) { const m = el.textContent.trim().match(/^(https?:\/\/[^\s]+)$/); if (m) el.innerHTML = `<a href="${m[1]}" target="_blank" rel="noopener">${m[1]}</a>`; } });

  // Scroll to top visibility toggle
  const backTop = document.querySelector('.back-top');
  if (backTop) {
    const checkScroll = () => { backTop.classList.toggle('is-visible', window.scrollY > 300); };
    window.addEventListener('scroll', checkScroll, { passive: true });
    checkScroll();
  }

  // Horizontal rail smooth navigation buttons with RTL awareness and state updates
  document.querySelectorAll('.home-rail').forEach(rail => {
    const grid = rail.querySelector('.card-grid');
    const prevBtn = rail.querySelector('[data-rail-dir="prev"]');
    const nextBtn = rail.querySelector('[data-rail-dir="next"]');
    if (!grid) return;

    const updateButtons = () => {
      const maxScroll = grid.scrollWidth - grid.clientWidth;
      const cur = Math.abs(grid.scrollLeft);
      if (prevBtn) prevBtn.disabled = cur <= 2;
      if (nextBtn) nextBtn.disabled = cur >= maxScroll - 2;
    };

    grid.addEventListener('scroll', updateButtons, { passive: true });
    updateButtons();

    [prevBtn, nextBtn].forEach(btn => {
      if (!btn) return;
      btn.addEventListener('click', () => {
        const dir = btn.dataset.railDir;
        const step = grid.clientWidth * 0.8;
        grid.scrollBy({ left: dir === 'next' ? -step : step, behavior: 'smooth' });
        setTimeout(updateButtons, 350);
      });
    });
  });

  // Event gallery toggle
  const galleryToggle = document.querySelector('[data-gallery-toggle]');
  if (galleryToggle) {
    galleryToggle.addEventListener('click', () => {
      const gal = document.querySelector('#event-gallery');
      if (!gal) return;
      const expanded = gal.classList.toggle('is-expanded');
      galleryToggle.setAttribute('aria-expanded', String(expanded));
      galleryToggle.textContent = expanded ? 'طي معرض الصور ▴' : `عرض جميع الفعاليات (${gal.querySelectorAll('figure').length}) ▾`;
    });
  }

  // Visually style raw URL excerpts
  document.querySelectorAll('.card-excerpt').forEach(el => {
    if (/^https?:\/\/[^\s]+$/.test(el.textContent.trim())) {
      el.classList.add('is-raw-url-excerpt');
    }
  });

  // Dynamic Hero Carousel (Full-Row with Auto-Play & Navigation)
  const slider = document.querySelector('#home-slider');
  if (slider) {
    const slides = Array.from(slider.querySelectorAll('.home-slide'));
    const dots = Array.from(slider.querySelectorAll('.slider-dot'));
    let current = 0;
    let timer = null;

    const showSlide = (idx) => {
      current = (idx + slides.length) % slides.length;
      slides.forEach((s, i) => s.classList.toggle('is-active', i === current));
      dots.forEach((d, i) => d.classList.toggle('is-active', i === current));
    };

    slider.querySelector('[data-slide-dir="prev"]')?.addEventListener('click', () => {
      showSlide(current - 1);
      resetAuto();
    });

    slider.querySelector('[data-slide-dir="next"]')?.addEventListener('click', () => {
      showSlide(current + 1);
      resetAuto();
    });

    dots.forEach((d, i) => {
      d.addEventListener('click', () => {
        showSlide(i);
        resetAuto();
      });
    });

    const startAuto = () => {
      timer = setInterval(() => {
        showSlide(current + 1);
      }, 5000);
    };

    const resetAuto = () => {
      clearInterval(timer);
      startAuto();
    };

    slider.addEventListener('mouseenter', () => clearInterval(timer));
    slider.addEventListener('mouseleave', () => startAuto());

    startAuto();
  }

})();
