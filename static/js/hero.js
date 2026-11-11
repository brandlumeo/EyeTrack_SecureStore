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
