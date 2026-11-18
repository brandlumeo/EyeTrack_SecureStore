/* Premium UI layer: gentle scroll reveal. */

/* ---- Scroll reveal ----
   Only runs on pages with body.p-ui, skips anything the site already animates (.reveal),
   and does nothing for people who prefer reduced motion. Content is never hidden without JS. */
(function () {
    'use strict';
    var body = document.body;
    if (!body || !body.classList.contains('p-ui')) return;
    if (!('IntersectionObserver' in window)) return;
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    var selector = [
        '.main-shell .home-section',
        '.main-shell .glass-card',
        '.main-shell .protect-card',
        '.main-shell .process-step',
        '.main-shell .package-card',
        '.main-shell .testimonial-card',
        '.main-shell .solutions-card',
        '.main-shell .tool-card',
        '.main-shell .project-card',
        '.main-shell .guide-card',
        '.main-shell .st-section',
        '.main-shell .st-tip'
    ].join(',');

    var fold = window.innerHeight || document.documentElement.clientHeight;
    if (!fold || fold < 300) return; // can't tell what is on screen: leave everything as is
    var items = Array.prototype.filter.call(document.querySelectorAll(selector), function (el) {
        if (el.classList.contains('reveal') || el.closest('.reveal, .modal, .offcanvas, [hidden]')) return false;
        // Do not animate a card whose section is already being revealed.
        if (el.parentElement && el.parentElement.closest('.p-reveal')) return false;
        var rect = el.getBoundingClientRect();
        // Blocks taller than the screen are left alone; their cards animate individually instead.
        if (rect.height > fold * 0.9) return false;
        var keep = rect.top > fold * 0.92;
        if (keep) el.classList.add('p-reveal');
        return keep;
    });
    if (!items.length) return;

    // Stagger siblings that enter together (cards in a grid).
    var groups = new Map();
    items.forEach(function (el) {
        var key = el.parentElement;
        var i = groups.get(key) || 0;
        el.style.setProperty('--p-delay', Math.min(i, 5) * 70 + 'ms');
        groups.set(key, i + 1);
    });

    var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (!entry.isIntersecting) return;
            entry.target.classList.add('is-in');
            io.unobserve(entry.target);
        });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    items.forEach(function (el) { io.observe(el); });

    // Safety net: never leave content hidden (e.g. print, anchor jumps, very fast scrolling).
    window.addEventListener('beforeprint', function () { items.forEach(function (el) { el.classList.add('is-in'); }); });
    setTimeout(function () {
        items.forEach(function (el) {
            if (el.getBoundingClientRect().top < window.innerHeight) el.classList.add('is-in');
        });
    }, 2500);
})();
