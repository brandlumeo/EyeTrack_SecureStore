/* Homepage hero carousel: crossfade + slow zoom, autoplay that pauses on hover/focus. */
(() => {
    const controls = document.querySelector('.hero-3d__slides');
    if (!controls) return;

    const hero = controls.closest('.hero-3d');
    const images = hero.querySelectorAll('.hero-3d__backgrounds img');
    const buttons = controls.querySelectorAll('button');
    const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const INTERVAL = 6500;
    let current = 0;
    let timer = 0;
    let paused = false;

    const show = (index) => {
        current = (index + images.length) % images.length;
        images.forEach((image, i) => image.classList.toggle('is-current', i === current));
        buttons.forEach((button, i) => button.setAttribute('aria-pressed', String(i === current)));
        // restart the progress line on the active indicator
        hero.classList.remove('is-ticking');
        void hero.offsetWidth;
        if (!paused && !motion.matches) hero.classList.add('is-ticking');
    };

    const stop = () => { clearInterval(timer); timer = 0; };
    const start = () => {
        stop();
        if (paused || motion.matches || document.hidden) return;
        hero.classList.add('is-ticking');
        timer = setInterval(() => show(current + 1), INTERVAL);
    };
    const setPaused = (value) => {
        paused = value;
        hero.classList.toggle('is-paused', value);
        if (value) stop(); else start();
    };

    hero.style.setProperty('--h3d-interval', `${INTERVAL}ms`);
    buttons.forEach((button, index) => {
        button.addEventListener('click', () => { show(index); start(); });
    });
    hero.addEventListener('mouseenter', () => setPaused(true));
    hero.addEventListener('mouseleave', () => setPaused(false));
    hero.addEventListener('focusin', () => setPaused(true));
    hero.addEventListener('focusout', (event) => {
        if (!hero.contains(event.relatedTarget)) setPaused(false);
    });
    document.addEventListener('visibilitychange', () => (document.hidden ? stop() : start()));
    motion.addEventListener('change', () => { hero.classList.remove('is-ticking'); start(); });

    controls.hidden = false;
    show(0);
    start();
})();
