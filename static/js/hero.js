(() => {
    const stage = document.getElementById('hero3dStage');
    if (!stage) return;
    const hero = stage.closest('.hero-3d');
    const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
    let frame = 0;
    // Model build: wireframe -> extrude -> materials -> render (timed in hero.css).
    const face = hero.querySelector('.hero-3d__face');
    const wire = hero.querySelector('.hero-3d__wire');
    const stepEl = document.getElementById('hero3dStep');
    const pctEl = document.getElementById('hero3dPct');
    const progress = hero.querySelector('.hero-3d__hud-progress');
    const BUILD_SECONDS = 4.2;
    const STEPS = [
        [0, 'Initialising'], [0.35, 'Wireframe'], [1.45, 'Extruding depth'],
        [2.35, 'Applying materials'], [3.5, 'Final render'], [BUILD_SECONDS, 'Render complete'],
    ];
    const loaded = (img) => !img || (img.complete && img.naturalWidth > 0);
    const reveal = () => hero.classList.remove('hero-3d--pending');
    if (motion.matches) reveal();
    // Never keep the stage hidden: show the finished logo if images are slow.
    let gaveUp = false;
    setTimeout(() => {
        if (!hero.classList.contains('hero-3d--build')) { gaveUp = true; reveal(); }
    }, 8000);
    const startBuild = () => {
        if (gaveUp || motion.matches || hero.classList.contains('hero-3d--build')) return reveal();
        hero.classList.add('hero-3d--build');
        reveal();
        // The HUD clock only advances while the CSS animations are running
        // (they rest while the hero is off-screen).
        let elapsed = 0;
        let last = performance.now();
        const tick = (now) => {
            const running = hero.dataset.offscreen !== 'true';
            if (running) elapsed += (now - last) / 1000;
            last = now;
            const t = Math.min(elapsed, BUILD_SECONDS);
            const step = STEPS.filter(([at]) => t >= at).pop();
            if (stepEl.textContent !== step[1]) stepEl.textContent = step[1];
            const pct = Math.round((t / BUILD_SECONDS) * 100);
            pctEl.textContent = `${pct}%`;
            progress.style.setProperty('--p', `${pct}%`);
            if (elapsed < BUILD_SECONDS) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
    };
    // Wait for both images so no layer pops in mid-build.
    const whenReady = () => { if (loaded(face) && loaded(wire)) startBuild(); };
    [face, wire].forEach((img) => img && !loaded(img) && img.addEventListener('load', whenReady, { once: true }));
    whenReady();
    const reset = () => {
        cancelAnimationFrame(frame);
        stage.style.setProperty('--tilt-x', '0deg');
        stage.style.setProperty('--tilt-y', '0deg');
    };
    hero.addEventListener('pointermove', (event) => {
        if (motion.matches || event.pointerType !== 'mouse') return;
        cancelAnimationFrame(frame);
        frame = requestAnimationFrame(() => {
            const rect = stage.getBoundingClientRect();
            const x = Math.max(-1, Math.min(1, (event.clientX - rect.left) / rect.width * 2 - 1));
            const y = Math.max(-1, Math.min(1, (event.clientY - rect.top) / rect.height * 2 - 1));
            stage.style.setProperty('--tilt-y', `${x * 8}deg`);
            stage.style.setProperty('--tilt-x', `${y * -6}deg`);
        });
    });
    hero.addEventListener('pointerleave', reset);
    motion.addEventListener('change', reset);
    if ('IntersectionObserver' in window) {
        new IntersectionObserver(([entry]) => {
            hero.dataset.offscreen = String(!entry.isIntersecting);
        }).observe(hero);
    }
})();

(() => {
    const controls = document.querySelector('.hero-3d__slides');
    if (!controls) return;

    const images = controls.closest('.hero-3d').querySelectorAll('.hero-3d__backgrounds img');
    const buttons = controls.querySelectorAll('button');
    buttons.forEach((button, index) => {
        button.addEventListener('click', () => {
            images.forEach((image, position) => image.classList.toggle('is-current', position === index));
            buttons.forEach((item, position) => item.setAttribute('aria-pressed', String(position === index)));
        });
    });
    controls.hidden = false;
})();
