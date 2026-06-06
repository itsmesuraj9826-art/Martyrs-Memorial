/* animations.js — Gallery, lightbox, stagger animations */
(function () {
  'use strict';

  /* ══ Force-show all gallery elements — never let them go opacity:0 ══ */
  function forceVisible(selector) {
    document.querySelectorAll(selector).forEach(el => {
      el.classList.add('is-visible');
      el.style.opacity   = '1';
      el.style.transform = 'none';
    });
  }

  forceVisible('.photo-item');
  forceVisible('.photo-grid .photo-item');
  forceVisible('.album-card');
  forceVisible('.albums-grid .album-card');
  forceVisible('.gallery-thumb');

  /* ══ Stagger animation for homepage grids ONLY ══ */
  const isHomepage = document.querySelector('.hero') !== null;
  if (isHomepage) {
    document.querySelectorAll('.events-grid, .news-grid, .testimonials-slider').forEach(grid => {
      Array.from(grid.children).forEach((child, i) => {
        child.style.transitionDelay = `${i * 0.08}s`;
        if (!child.classList.contains('is-visible')) {
          child.setAttribute('data-animate', 'fadeInUp');
          if ('IntersectionObserver' in window) {
            const obs = new IntersectionObserver((entries) => {
              entries.forEach(e => {
                if (e.isIntersecting) {
                  e.target.classList.add('is-visible');
                  obs.unobserve(e.target);
                }
              });
            }, { threshold: 0.10 });
            obs.observe(child);
          } else {
            child.classList.add('is-visible');
          }
        }
      });
    });
  }

})();