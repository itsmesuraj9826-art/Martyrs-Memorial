/* ============================================================
   main.js — Public site interactivity
   School Website — Greenwood Academy
   ============================================================ */
(function () {
  'use strict';

  /* ══════════════════════════════════════════════════════
     Dark / Light mode  +  Live Clock  +  Auto time-switch
     ══════════════════════════════════════════════════════
     Logic:
       - AUTO mode (default): dark from 18:00–05:59, light 06:00–17:59
       - Manual click on toggle → overrides auto for the session
       - localStorage key "themeOverride" stores manual choice
       - localStorage key "themeOverrideExpiry" stores expiry (next midnight)
         so the override resets automatically next day
  ═══════════════════════════════════════════════════════ */

  const themeToggle  = document.getElementById('themeToggle');
  const themeIcon    = themeToggle?.querySelector('.theme-icon');
  const clockTimeEl  = document.getElementById('clockTime');
  const clockAmPmEl  = document.getElementById('clockAmPm');
  const clockAutoEl  = document.getElementById('clockAutoLabel');

  // Is it naturally a dark hour? (18:00 – 05:59)
  function isNightHour(h) { return h >= 18 || h < 6; }

  // Apply theme to DOM
  function applyTheme(dark) {
    document.body.classList.toggle('dark-mode', dark);
    document.body.classList.toggle('light-mode', !dark);
    if (themeIcon) themeIcon.textContent = dark ? '☀️' : '🌙';
    if (themeToggle) themeToggle.setAttribute('aria-pressed', dark ? 'true' : 'false');
  }

  // Check if manual override has expired (past midnight)
  function overrideExpired() {
    const exp = parseInt(localStorage.getItem('themeOverrideExpiry') || '0', 10);
    return Date.now() > exp;
  }

  // Clear override so auto mode resumes
  function clearOverride() {
    localStorage.removeItem('themeOverride');
    localStorage.removeItem('themeOverrideExpiry');
  }

  // Manual toggle click — set override until next midnight
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const dark = !document.body.classList.contains('dark-mode');
      applyTheme(dark);
      // Expire at next midnight
      const now    = new Date();
      const expiry = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1, 0, 0, 0).getTime();
      localStorage.setItem('themeOverride',       dark ? 'dark' : 'light');
      localStorage.setItem('themeOverrideExpiry', String(expiry));
      if (clockAutoEl) clockAutoEl.style.opacity = '0.35'; // dim AUTO label
    });
  }

  /* ── Clock tick — runs every second ── */
  function tick() {
    const now  = new Date();
    const h24  = now.getHours();
    const min  = now.getMinutes();
    const sec  = now.getSeconds();
    const h12  = h24 % 12 || 12;
    const ampm = h24 < 12 ? 'AM' : 'PM';

    if (clockTimeEl) clockTimeEl.textContent = String(h12).padStart(2,'0') + ':' + String(min).padStart(2,'0') + ':' + String(sec).padStart(2,'0');
    if (clockAmPmEl) clockAmPmEl.textContent = ampm;

    // Auto theme switch — only when no manual override is active
    if (overrideExpired()) {
      clearOverride();
      applyTheme(isNightHour(h24));
      if (clockAutoEl) { clockAutoEl.style.opacity = '1'; clockAutoEl.title = 'Auto mode active'; }
    }
  }

  // Initial state on load
  (function init() {
    if (!overrideExpired()) {
      // Honour unexpired manual override
      const override = localStorage.getItem('themeOverride');
      applyTheme(override === 'dark');
      if (clockAutoEl) clockAutoEl.style.opacity = '0.35';
    } else {
      clearOverride();
      // Auto: use time of day
      applyTheme(isNightHour(new Date().getHours()));
    }
  })();

  tick(); // render clock immediately
  setInterval(tick, 1000);

  /* ── Ticker close ── */
  const tickerClose = document.getElementById('tickerClose');
  if (tickerClose) {
    tickerClose.addEventListener('click', () => {
      document.body.classList.add('ticker-hidden');
      sessionStorage.setItem('tickerClosed', '1');
    });
  }
  if (sessionStorage.getItem('tickerClosed') === '1') {
    document.body.classList.add('ticker-hidden');
  }

  /* ── Hero stat card counters ── */
  function animateCounter(el) {
    const target = parseInt(el.dataset.target || '0', 10);
    const dur    = 1600;
    const step   = 16;
    const inc    = target / (dur / step);
    let   cur    = 0;
    const t = setInterval(() => {
      cur = Math.min(cur + inc, target);
      el.textContent = Math.floor(cur);
      if (cur >= target) clearInterval(t);
    }, step);
  }
  const heroSection = document.getElementById('heroSection');
  if (heroSection) {
    const obs = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        heroSection.querySelectorAll('.hsc-num').forEach(animateCounter);
        obs.disconnect();
      }
    }, { threshold: 0.3 });
    obs.observe(heroSection);
  }

  /* ── Navbar scroll ── */
  const navbar = document.getElementById('navbar');
  if (navbar) {
    const updateNav = () => navbar.classList.toggle('scrolled', window.scrollY > 60);
    window.addEventListener('scroll', updateNav, { passive: true });
    updateNav();
  }

  /* ── Mobile nav toggle ── */
  const navToggle = document.getElementById('navToggle');
  const navLinks  = document.getElementById('navLinks');
  if (navToggle && navLinks) {
    navToggle.addEventListener('click', () => {
      const open = navLinks.classList.toggle('open');
      navToggle.setAttribute('aria-expanded', String(open));
      const spans = navToggle.querySelectorAll('span');
      if (open) {
        spans[0].style.cssText = 'transform:translateY(7px) rotate(45deg)';
        spans[1].style.cssText = 'opacity:0;transform:scaleX(0)';
        spans[2].style.cssText = 'transform:translateY(-7px) rotate(-45deg)';
      } else {
        spans.forEach(s => s.style.cssText = '');
      }
    });
    document.addEventListener('click', (e) => {
      if (navbar && !navbar.contains(e.target)) {
        navLinks.classList.remove('open');
        navToggle.querySelectorAll('span').forEach(s => s.style.cssText = '');
      }
    });
  }

  /* ── Scroll reveal animations ── */
  const animEls = document.querySelectorAll('[data-animate]');
  if (animEls.length && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('is-visible');
          observer.unobserve(e.target);
        }
      });
    }, { threshold: 0.10, rootMargin: '0px 0px -40px 0px' });
    animEls.forEach(el => observer.observe(el));
  } else {
    animEls.forEach(el => el.classList.add('is-visible'));
  }

  /* ── Animated stat counters ── */
  function animateCounter(el, target, duration) {
    const start   = performance.now();
    const easeOut = t => 1 - Math.pow(1 - t, 3);
    function step(now) {
      const progress = Math.min((now - start) / duration, 1);
      el.textContent = Math.round(easeOut(progress) * target);
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }
  const counterEls = document.querySelectorAll('.stat-number[data-target]');
  if (counterEls.length && 'IntersectionObserver' in window) {
    const cObs = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          animateCounter(e.target, parseInt(e.target.dataset.target, 10), 1800);
          cObs.unobserve(e.target);
        }
      });
    }, { threshold: 0.5 });
    counterEls.forEach(el => cObs.observe(el));
  }

  /* ── Auto-dismiss flash messages ── */
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity .4s ease, transform .4s ease';
      el.style.opacity    = '0';
      el.style.transform  = 'translateX(20px)';
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });

  /* ── Current year ── */
  document.querySelectorAll('[data-year]').forEach(el => {
    el.textContent = new Date().getFullYear();
  });

})();