(() => {
    const navigation = document.querySelector('.hero-3d__navigation');
    if (!navigation) return;

    const hero = navigation.closest('.hero-3d');
    const photos = hero.querySelectorAll('.hero-3d__backgrounds img');
    const stories = hero.querySelectorAll('[data-hero-story]');
    const buttons = navigation.querySelectorAll('.hero-3d__slides button');
    const status = navigation.querySelector('[data-hero-status]');
    const pause = navigation.querySelector('[data-hero-pause]');
    const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
    let current = 0;
    let timer;
    let paused = false;

    const show = (index, announce = false) => {
        current = (index + photos.length) % photos.length;
        photos.forEach((photo, i) => photo.classList.toggle('is-current', i === current));
        stories.forEach((story, i) => { story.hidden = i !== current; });
        buttons.forEach((button, i) => button.setAttribute('aria-pressed', String(i === current)));
        if (announce) status.textContent = buttons[current].textContent;
    };

    const schedule = () => {
        clearTimeout(timer);
        pause.hidden = motion.matches;
        pause.textContent = paused ? 'Play' : 'Pause';
        if (paused || motion.matches || document.hidden || hero.matches(':hover, :focus-within')) return;
        timer = setTimeout(() => {
            show(current + 1);
            schedule();
        }, 7000);
    };

    const select = (index) => {
        paused = true;
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

    navigation.hidden = false;
    schedule();
})();
