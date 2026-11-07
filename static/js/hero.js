(() => {
    const stage = document.getElementById('hero3dStage');
    if (!stage) return;
    const hero = stage.closest('.hero-3d');
    const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const button = hero.querySelector('.hero-3d__motion');
    let paused = false;
    let frame = 0;
    // Assemble six clipped sections of the original artwork without altering it.
    const logo = hero.querySelector('.hero-3d__logo');
    const face = logo.querySelector('.hero-3d__face');
    const assemble = () => {
        if (motion.matches || hero.classList.contains('hero-3d--assemble')) return;
        const fragments = document.createElement('span');
        fragments.className = 'hero-3d__fragments';
        fragments.setAttribute('aria-hidden', 'true');
        for (let i = 0; i < 6; i++) {
            const piece = face.cloneNode();
            piece.className = 'hero-3d__fragment';
            piece.alt = '';
            piece.style.setProperty('--slice', i);
            piece.style.setProperty('--from-x', `${i % 2 ? 90 : -90}%`);
            piece.style.setProperty('--from-y', `${(i - 2.5) * 24}px`);
            piece.style.setProperty('--turn', `${i % 2 ? 24 : -24}deg`);
            fragments.appendChild(piece);
        }
        logo.appendChild(fragments);
        hero.classList.add('hero-3d--assemble');
    };
    // Wait for the artwork so the reveal never runs before the logo is ready.
    if (face.complete && face.naturalWidth) assemble();
    else face.addEventListener('load', assemble, { once: true });
    button.hidden = false;
    button.addEventListener('click', () => {
        paused = !paused;
        hero.dataset.paused = String(paused);
        button.setAttribute('aria-pressed', String(paused));
        button.setAttribute('aria-label', `${paused ? 'Resume' : 'Pause'} logo animation`);
        button.querySelector('.hero-3d__motion-label').textContent = `${paused ? 'Resume' : 'Pause'} animation`;
        button.firstElementChild.textContent = paused ? '▷' : 'Ⅱ';
    });
    const reset = () => {
        cancelAnimationFrame(frame);
        stage.style.setProperty('--tilt-x', '0deg');
        stage.style.setProperty('--tilt-y', '0deg');
    };
    hero.addEventListener('pointermove', (event) => {
        if (paused || motion.matches || event.pointerType !== 'mouse') return;
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
