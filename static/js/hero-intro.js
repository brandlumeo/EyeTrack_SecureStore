/* Homepage brand intro: the hero plays the intro video, the logo appears over it,
   then the logo flies into the navbar logo and the banner carousel takes over.
   Runs once per session (decided inline in product_list.html). */
(() => {
    const intro = document.querySelector('[data-hero-intro]');
    if (!intro || intro.hidden) return;

    const root = document.documentElement;
    const hero = intro.closest('.hero-3d');
    const video = intro.querySelector('video');
    const brand = intro.querySelector('.hero-intro__brand');
    const logo = intro.querySelector('.hero-intro__logo');
    const skip = intro.querySelector('[data-hero-intro-skip]');
    // desktop navbar logo, or on phones the logo in the mobile menu bar's Home item
    const logoTargets = [...document.querySelectorAll('#siteHeader .brand-logo, #dockHome .dock-logo')];
    const isShown = (el) => {
        const r = el.getBoundingClientRect();
        if (!el.offsetHeight || r.bottom < 0 || r.top > window.innerHeight) return false;
        const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
        return !!hit && (hit === el || el.contains(hit) || hit.contains(el));
    };
    let navLogo = null;

    const LOGO_HOLD = 1300;   // logo stays centred before it flies
    const FLY = 1050;         // flight into the navbar
    const SAFETY = 10000;     // never let the intro hang (slow network, stalled video)

    let stage = 'video';
    let safety = 0;
    let holdTimer = 0;
    let flyer = null;

    const finish = () => {
        if (stage === 'done') return;
        stage = 'done';
        clearTimeout(safety);
        clearTimeout(holdTimer);
        video.pause();
        root.classList.remove('intro-on');
        if (navLogo) {
            navLogo.classList.add('is-landed');
            setTimeout(() => navLogo.classList.remove('is-landed'), 700);
        }
        intro.classList.add('is-out');
        hero.classList.remove('is-intro');
        hero.dispatchEvent(new Event('heroIntroEnd'));
        setTimeout(() => {
            intro.remove();
            if (flyer) flyer.remove();
        }, 900);
    };

    const fly = () => {
        if (stage !== 'logo') return;
        stage = 'fly';
        navLogo = logoTargets.find(isShown) || null;
        const to = navLogo ? navLogo.getBoundingClientRect() : null;
        const from = logo.getBoundingClientRect();
        // navbar logo hidden (e.g. collapsed layout) or scrolled away: just fade out
        if (!to || !to.width || to.bottom < 0 || !from.width || typeof logo.animate !== 'function') {
            finish();
            return;
        }

        // the stage clips its content, so the logo flies as a fixed copy above the header
        flyer = logo.cloneNode();
        flyer.className = 'hero-intro__flyer';
        Object.assign(flyer.style, {
            left: `${from.left}px`, top: `${from.top}px`,
            width: `${from.width}px`, height: `${from.height}px`,
        });
        document.body.appendChild(flyer);
        logo.style.visibility = 'hidden';
        intro.classList.add('is-flying');

        // the navbar logo is scaled down while it waits, so size by its layout box, not its rect
        const scale = (navLogo.offsetHeight * 0.86) / from.height;
        const dx = (to.left + to.width / 2) - (from.left + from.width / 2);
        const dy = (to.top + to.height / 2) - (from.top + from.height / 2);
        const flight = flyer.animate([
            { transform: 'translate(0, 0) scale(1) rotate(0deg)', offset: 0 },
            { transform: `translate(${dx * 0.42}px, ${dy * 0.3}px) scale(${0.55 + scale * 0.45}) rotate(-8deg)`, offset: 0.45 },
            { transform: `translate(${dx}px, ${dy}px) scale(${scale}) rotate(0deg)`, offset: 1 },
        ], { duration: FLY, easing: 'cubic-bezier(.65, 0, .25, 1)', fill: 'forwards' });

        // reveal the carousel while the logo is still travelling
        setTimeout(() => intro.classList.add('is-out'), FLY * 0.35);

        flight.finished.then(() => {
            finish();
            flyer.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 260, fill: 'forwards' });
        }).catch(finish);
    };

    const showLogo = () => {
        if (stage !== 'video') return;
        stage = 'logo';
        intro.classList.add('is-logo');
        holdTimer = setTimeout(fly, LOGO_HOLD);
    };

    const start = () => {
        safety = setTimeout(() => {
            if (stage === 'video') showLogo();
            else finish();
        }, SAFETY);
        video.addEventListener('ended', showLogo, { once: true });
        video.addEventListener('error', showLogo, { once: true });
        const play = video.play();
        if (play && typeof play.catch === 'function') play.catch(showLogo);
    };

    skip.addEventListener('click', finish);
    brand.addEventListener('click', () => { if (stage === 'logo') { clearTimeout(holdTimer); fly(); } });

    // wait for the first-visit preloader to clear, otherwise the video plays unseen behind it
    if (root.classList.contains('pl-on')) {
        const watch = new MutationObserver(() => {
            if (!root.classList.contains('pl-on')) {
                watch.disconnect();
                start();
            }
        });
        watch.observe(root, { attributes: true, attributeFilter: ['class'] });
    } else {
        start();
    }
})();
