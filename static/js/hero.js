/* Homepage hero: full-width banner carousel (slide track, arrows, pill dots, swipe). */
(() => {
    const hero = document.querySelector('.hero-3d');
    if (!hero) return;

    const track = hero.querySelector('.hero-3d__track');
    const slides = hero.querySelectorAll('.hero-3d__slide');
    const navigation = hero.querySelector('.hero-3d__navigation');
    const dots = navigation.querySelectorAll('.hero-3d__slides button');
    const status = navigation.querySelector('[data-hero-status]');
    const arrows = hero.querySelectorAll('.hero-3d__arrow');
    const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const INTERVAL = 6000;
    const total = slides.length;
    let current = 0;
    let timer = 0;
    let remaining = INTERVAL;
    let startedAt = 0;

    hero.style.setProperty('--h3d-interval', `${INTERVAL}ms`);

    // full-bleed width minus the scrollbar (100vw counts it on desktop)
    const setScrollbar = () => hero.style.setProperty('--h3d-sbw', `${Math.max(0, window.innerWidth - document.documentElement.clientWidth)}px`);
    setScrollbar();
    window.addEventListener('resize', setScrollbar, { passive: true });

    const show = (index, announce = false) => {
        current = (index + total) % total;
        track.style.transform = `translateX(${-current * 100}%)`;
        slides.forEach((slide, i) => {
            const active = i === current;
            slide.classList.toggle('is-current', active);
            slide.toggleAttribute('inert', !active);
            slide.setAttribute('aria-hidden', String(!active));
        });
        dots.forEach((dot, i) => dot.setAttribute('aria-pressed', String(i === current)));
        if (announce) status.textContent = slides[current].getAttribute('aria-label') + ': ' + slides[current].querySelector('h2').textContent;
        // restart the pill's progress fill
        hero.classList.remove('is-ticking');
        void hero.offsetWidth;
        hero.classList.add('is-ticking');
        remaining = INTERVAL;
    };

    const halted = () => motion.matches || document.hidden || hero.matches(':hover, :focus-within');

    const schedule = () => {
        clearTimeout(timer);
        if (halted()) {
            if (startedAt) remaining = Math.max(0, remaining - (performance.now() - startedAt));
            startedAt = 0;
            hero.classList.add('is-halted');
            return;
        }
        hero.classList.remove('is-halted');
        startedAt = performance.now();
        timer = setTimeout(() => {
            startedAt = 0;
            show(current + 1);
            schedule();
        }, remaining);
    };

    const go = (index) => {
        startedAt = 0;
        show(index, true);
        schedule();
    };

    dots.forEach((dot, i) => dot.addEventListener('click', () => go(i)));
    hero.querySelector('[data-hero-prev]').addEventListener('click', () => go(current - 1));
    hero.querySelector('[data-hero-next]').addEventListener('click', () => go(current + 1));

    // swipe on touch screens
    let startX = null;
    track.addEventListener('pointerdown', (event) => {
        if (event.pointerType !== 'mouse') startX = event.clientX;
    });
    track.addEventListener('pointerup', (event) => {
        if (startX === null) return;
        const dx = event.clientX - startX;
        startX = null;
        if (Math.abs(dx) > 40) go(current + (dx < 0 ? 1 : -1));
    });
    track.addEventListener('pointercancel', () => { startX = null; });

    hero.addEventListener('mouseenter', schedule);
    hero.addEventListener('mouseleave', schedule);
    hero.addEventListener('focusin', schedule);
    hero.addEventListener('focusout', () => setTimeout(schedule, 0));
    document.addEventListener('visibilitychange', schedule);
    motion.addEventListener('change', schedule);

    arrows.forEach((arrow) => { arrow.hidden = false; });
    navigation.hidden = false;
    show(0);
    schedule();
})();
