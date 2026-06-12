/* ============================================================
   facility-lightbox.js
   Click a facility card → photo lightbox of the matching
   Gallery album (album name must equal the facility title).
   Cards with no matching album stay non-clickable.
   ============================================================ */
(function () {
  'use strict';

  var cards = document.querySelectorAll('.facility-card');
  if (!cards.length) return; // not on this page — exit silently

  var albumMap = null;

  // Fetch published album name→id map once
  fetch('/api/facility-albums')
    .then(function (r) { return r.json(); })
    .then(function (map) {
      albumMap = map || {};
      cards.forEach(function (card) {
        var h3 = card.querySelector('h3');
        if (!h3) return;
        var key = h3.textContent.trim().toLowerCase();
        if (albumMap[key]) {
          card.classList.add('facility-clickable');
          card.setAttribute('role', 'button');
          card.setAttribute('tabindex', '0');
          card.dataset.albumId = albumMap[key];
          card.addEventListener('click', function () { openLightbox(card.dataset.albumId, h3.textContent.trim()); });
          card.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              openLightbox(card.dataset.albumId, h3.textContent.trim());
            }
          });
          // small camera hint badge
          var hint = document.createElement('span');
          hint.className = 'facility-photo-hint';
          hint.innerHTML = '<i class="fa-solid fa-camera"></i> View photos';
          card.appendChild(hint);
        }
      });
    })
    .catch(function () { /* API unavailable — cards stay normal */ });

  /* ── Lightbox ── */
  var lb = null, photos = [], idx = 0;

  function buildLightbox() {
    lb = document.createElement('div');
    lb.className = 'flb-overlay';
    lb.innerHTML =
      '<div class="flb-box" role="dialog" aria-modal="true">' +
      '  <div class="flb-head">' +
      '    <span class="flb-title"></span>' +
      '    <button class="flb-close" aria-label="Close">×</button>' +
      '  </div>' +
      '  <div class="flb-stage">' +
      '    <button class="flb-nav flb-prev" aria-label="Previous">‹</button>' +
      '    <img class="flb-img" alt="">' +
      '    <button class="flb-nav flb-next" aria-label="Next">›</button>' +
      '  </div>' +
      '  <div class="flb-caption"></div>' +
      '  <div class="flb-count"></div>' +
      '</div>';
    document.body.appendChild(lb);

    lb.querySelector('.flb-close').addEventListener('click', closeLightbox);
    lb.querySelector('.flb-prev').addEventListener('click', function () { show(idx - 1); });
    lb.querySelector('.flb-next').addEventListener('click', function () { show(idx + 1); });
    lb.addEventListener('click', function (e) { if (e.target === lb) closeLightbox(); });
    document.addEventListener('keydown', function (e) {
      if (!lb || !lb.classList.contains('flb-open')) return;
      if (e.key === 'Escape')      closeLightbox();
      if (e.key === 'ArrowLeft')   show(idx - 1);
      if (e.key === 'ArrowRight')  show(idx + 1);
    });

    /* Touch swipe */
    var startX = 0;
    var stage = lb.querySelector('.flb-stage');
    stage.addEventListener('touchstart', function (e) { startX = e.touches[0].clientX; }, { passive: true });
    stage.addEventListener('touchend', function (e) {
      var diff = startX - e.changedTouches[0].clientX;
      if (Math.abs(diff) > 50) show(idx + (diff > 0 ? 1 : -1));
    }, { passive: true });
  }

  function openLightbox(albumId, title) {
    if (!lb) buildLightbox();
    lb.querySelector('.flb-title').textContent = title;
    lb.querySelector('.flb-img').src = '';
    lb.querySelector('.flb-caption').textContent = 'Loading…';
    lb.querySelector('.flb-count').textContent = '';
    lb.classList.add('flb-open');
    document.body.style.overflow = 'hidden';

    fetch('/api/facility-photos/' + albumId)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        photos = data.photos || [];
        if (!photos.length) {
          lb.querySelector('.flb-caption').textContent = 'Photos coming soon.';
          return;
        }
        show(0);
      })
      .catch(function () {
        lb.querySelector('.flb-caption').textContent = 'Could not load photos.';
      });
  }

  function show(i) {
    if (!photos.length) return;
    idx = (i + photos.length) % photos.length;
    var p = photos[idx];
    var img = lb.querySelector('.flb-img');
    img.style.opacity = '0';
    var pre = new Image();
    pre.onload = function () {
      img.src = p.src;
      img.style.opacity = '1';
    };
    pre.src = p.src;
    lb.querySelector('.flb-caption').textContent = p.caption || '';
    lb.querySelector('.flb-count').textContent = (idx + 1) + ' / ' + photos.length;
    var multi = photos.length > 1;
    lb.querySelector('.flb-prev').style.display = multi ? '' : 'none';
    lb.querySelector('.flb-next').style.display = multi ? '' : 'none';
  }

  function closeLightbox() {
    lb.classList.remove('flb-open');
    document.body.style.overflow = '';
    photos = []; idx = 0;
  }
})();
