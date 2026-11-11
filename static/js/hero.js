/* Homepage hero: photo deck carousel with synced progress, pause on hover/focus. */
(() => {
    const navigation = document.querySelector('.hero-3d__navigation');
    if (!navigation) return;

    const hero = navigation.closest('.hero-3d');
    const photos = hero.querySelectorAll('.hero-3d__backgrounds img');
    const stories = hero.querySelectorAll('[data-hero-story]');
    const buttons = navigation.querySelectorAll('.hero-3d__slides button');
    const status = navigation.querySelector('[data-hero-status]');
    const pause = navigation.querySelector('[data-hero-pause]');
    const cam = hero.querySelector('[data-hero-cam]');
    const label = hero.querySelector('[data-hero-label]');
    const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const INTERVAL = 7000;
    const total = photos.length;
    let current = 0;
    let timer = 0;
    let remaining = INTERVAL;
    let startedAt = 0;
    let paused = false;

    hero.style.setProperty('--h3d-interval', `${INTERVAL}ms`);

    const labelOf = (i) => buttons[i].textContent.replace(/^\d+/, '').trim();

    const show = (index, announce = false) => {
        current = (index + total) % total;
        photos.forEach((photo, i) => {
            const offset = (i - current + total) % total;
            photo.classList.toggle('is-current', offset === 0);
            photo.classList.toggle('is-next', offset === 1);
            photo.classList.toggle('is-prev', offset === total - 1 && total > 2);
        });
        stories.forEach((story, i) => { story.hidden = i !== current; });
        buttons.forEach((button, i) => button.setAttribute('aria-pressed', String(i === current)));
        if (cam) cam.textContent = `CAM 0${current + 1}`;
        if (label) label.textContent = labelOf(current);
        if (announce) status.textContent = labelOf(current);
        // restart the progress line and the scan sweep
        hero.classList.remove('is-changing');
        void hero.offsetWidth;
        hero.classList.add('is-changing');
        remaining = INTERVAL;
    };

    const halted = () => paused || motion.matches || document.hidden || hero.matches(':hover, :focus-within');

    const schedule = () => {
        clearTimeout(timer);
        pause.hidden = motion.matches;
        pause.textContent = paused ? 'Play' : 'Pause';
        pause.setAttribute('aria-pressed', String(paused));
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

    const select = (index) => {
        paused = true;
        startedAt = 0;
        show(index, true);
        schedule();
    };

    buttons.forEach((button, index) => button.addEventListener('click', () => select(index)));
    navigation.querySelector('[data-hero-prev]').addEventListener('click', () => select(current - 1));
    navigation.querySelector('[data-hero-next]').addEventListener('click', () => select(current + 1));
    pause.addEventListener('click', () => {
        paused = !paused;
        schedule();
    });
    hero.addEventListener('mouseenter', schedule);
    hero.addEventListener('mouseleave', schedule);
    hero.addEventListener('focusin', schedule);
    hero.addEventListener('focusout', () => setTimeout(schedule, 0));
    document.addEventListener('visibilitychange', schedule);
    motion.addEventListener('change', schedule);

    // subtle 3D tilt of the photo deck following the pointer
    const deck = hero.querySelector('.hero-3d__deck');
    if (deck) {
        let frame = 0;
        hero.addEventListener('pointermove', (event) => {
            if (motion.matches || event.pointerType !== 'mouse') return;
            cancelAnimationFrame(frame);
            frame = requestAnimationFrame(() => {
                const rect = hero.getBoundingClientRect();
                const x = (event.clientX - rect.left) / rect.width - 0.5;
                const y = (event.clientY - rect.top) / rect.height - 0.5;
                hero.style.setProperty('--h3d-tilt-y', `${(x * 8).toFixed(2)}deg`);
                hero.style.setProperty('--h3d-tilt-x', `${(y * -6).toFixed(2)}deg`);
            });
        });
        hero.addEventListener('pointerleave', () => {
            cancelAnimationFrame(frame);
            hero.style.setProperty('--h3d-tilt-y', '0deg');
            hero.style.setProperty('--h3d-tilt-x', '0deg');
        });
    }

    navigation.hidden = false;
    show(0);
    schedule();
})();
