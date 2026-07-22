/**
 * Vincere RT — interação, conversão WhatsApp, FAQ, motion
 */
(function () {
  const WA = '5511917311001';
  const WA_BASE = `https://wa.me/${WA}`;

  function waUrl(message) {
    return `${WA_BASE}?text=${encodeURIComponent(message)}`;
  }

  // Expose for triage buttons
  window.VincereWA = { url: waUrl, number: WA };

  /* Header scroll */
  const header = document.querySelector('.site-header');
  if (header) {
    const onScroll = () => {
      header.classList.toggle('is-scrolled', window.scrollY > 12);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* Mobile nav */
  const toggle = document.querySelector('.nav-toggle');
  const drawer = document.querySelector('.nav-drawer');
  if (toggle && drawer) {
    toggle.addEventListener('click', () => {
      const open = drawer.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', String(open));
      document.body.style.overflow = open ? 'hidden' : '';
    });
    drawer.querySelectorAll('a').forEach((a) => {
      a.addEventListener('click', () => {
        drawer.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
      });
    });
  }

  /* Reveal on scroll */
  const reveals = document.querySelectorAll('[data-reveal]');
  if (reveals.length && 'IntersectionObserver' in window) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add('is-visible');
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -8% 0px' }
    );
    reveals.forEach((el) => io.observe(el));
  } else {
    reveals.forEach((el) => el.classList.add('is-visible'));
  }

  /* WhatsApp intent modal */
  const modal = document.getElementById('wa-modal');
  const openers = document.querySelectorAll('[data-wa-open]');
  const closers = document.querySelectorAll('[data-wa-close]');

  function openModal() {
    if (modal && typeof modal.showModal === 'function') modal.showModal();
  }

  function closeModal() {
    if (modal && modal.open) modal.close();
  }

  openers.forEach((btn) => btn.addEventListener('click', (e) => {
    e.preventDefault();
    openModal();
  }));

  closers.forEach((btn) => btn.addEventListener('click', closeModal));

  document.querySelectorAll('[data-wa-intent]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const intent = btn.getAttribute('data-wa-intent');
      const messages = {
        info: 'Olá, gostaria de informações gerais sobre a Residência Terapêutica Vincere em São Paulo.',
        admissao: 'Olá, gostaria de falar sobre admissão e vagas na Vincere Residência Terapêutica.',
        familia: 'Olá, sou familiar e preciso de orientação sobre tratamento na Vincere.',
        estrutura: 'Olá, gostaria de conhecer a estrutura e o modelo de cuidado da Vincere.',
      };
      const msg = messages[intent] || messages.info;
      window.open(waUrl(msg), '_blank', 'noopener,noreferrer');
      closeModal();
    });
  });

  /* Direct WA links with message */
  document.querySelectorAll('[data-wa-msg]').forEach((el) => {
    const msg = el.getAttribute('data-wa-msg');
    if (el.tagName === 'A') {
      el.setAttribute('href', waUrl(msg));
      el.setAttribute('target', '_blank');
      el.setAttribute('rel', 'noopener noreferrer');
    }
  });

  /* Triage */
  document.querySelectorAll('[data-triage]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const key = btn.getAttribute('data-triage');
      const map = {
        urgente: 'Olá, preciso de orientação urgente sobre acolhimento na Vincere Residência Terapêutica (São Paulo).',
        familiar: 'Olá, sou familiar e quero entender se a Vincere é adequada para o meu caso.',
        conhecer: 'Olá, quero conhecer o modelo de residência terapêutica particular da Vincere.',
      };
      window.open(waUrl(map[key] || map.conhecer), '_blank', 'noopener,noreferrer');
    });
  });

  /* Gallery lightbox */
  const lightbox = document.getElementById('lightbox');
  const lbFrame = document.getElementById('lightbox-frame');
  const lbCaption = document.getElementById('lightbox-caption');

  document.querySelectorAll('[data-gallery]').forEach((btn) => {
    btn.addEventListener('click', () => {
      if (!lightbox || !lbFrame) return;
      const title = btn.getAttribute('data-title') || '';
      const art = btn.querySelector('.g-art, svg');
      lbFrame.innerHTML = '';
      if (art) lbFrame.appendChild(art.cloneNode(true));
      if (lbCaption) lbCaption.textContent = title;
      if (typeof lightbox.showModal === 'function') lightbox.showModal();
    });
  });

  document.querySelectorAll('[data-lightbox-close]').forEach((btn) => {
    btn.addEventListener('click', () => lightbox && lightbox.close());
  });

  /* Prefetch key pages on hover */
  const prefetched = new Set();
  document.querySelectorAll('a[href$=".html"]').forEach((a) => {
    a.addEventListener(
      'pointerenter',
      () => {
        const href = a.getAttribute('href');
        if (!href || prefetched.has(href)) return;
        prefetched.add(href);
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = href;
        document.head.appendChild(link);
      },
      { once: true }
    );
  });

  /* Year */
  document.querySelectorAll('[data-year]').forEach((el) => {
    el.textContent = String(new Date().getFullYear());
  });
})();
