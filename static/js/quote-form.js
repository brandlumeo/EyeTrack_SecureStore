/* Site survey / quote form: AJAX submit and prefill from package & property cards. */
(function () {
    'use strict';

    function setPackage(form, name) {
        form.elements.package.value = name || '';
        var chip = form.querySelector('[data-quote-package-chip]');
        if (!chip) return;
        chip.classList.toggle('d-none', !name);
        chip.querySelector('[data-quote-package-label]').textContent = name || '';
    }

    // On pages with an inline survey form, cards prefill it instead of navigating to /get-quote/.
    document.addEventListener('click', function (e) {
        var trigger = e.target.closest('[data-quote-prefill]');
        var survey = document.getElementById('survey');
        if (!trigger || !survey) return;
        var form = survey.querySelector('[data-quote-form]');
        if (!form) return;
        e.preventDefault();
        if (trigger.dataset.siteType) form.elements.site_type.value = trigger.dataset.siteType;
        if (trigger.dataset.cameraCount) form.elements.camera_count.value = trigger.dataset.cameraCount;
        setPackage(form, trigger.dataset.package);
        survey.scrollIntoView({ behavior: 'smooth', block: 'start' });
        setTimeout(function () { form.elements.name.focus({ preventScroll: true }); }, 500);
    });

    document.querySelectorAll('[data-quote-form]').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            if (!window.fetch) return;
            e.preventDefault();
            var btn = form.querySelector('[data-quote-submit]');
            form.querySelectorAll('[data-error-for]').forEach(function (el) { el.textContent = ''; });
            btn.disabled = true;

            fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            }).then(function (r) { return r.json(); }).then(function (data) {
                btn.disabled = false;
                if (!data.ok) {
                    Object.keys(data.errors || {}).forEach(function (field) {
                        var el = form.querySelector('[data-error-for="' + field + '"]');
                        if (el) el.textContent = data.errors[field][0].message;
                    });
                    return;
                }
                form.reset();
                setPackage(form, '');
                var text = 'Our team will call you shortly to schedule your free site survey.';
                if (window.Swal) {
                    Swal.fire({
                        iconHtml: '<svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true"><path d="m8 16 5 5 11-11" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
                        icon: 'success',
                        titleText: 'Survey request received',
                        html: '<p class="quote-confirm-greeting"></p>' +
                            '<p class="quote-confirm-copy">Your safer space starts here. We\'ll call you shortly to arrange your free site survey.</p>' +
                            '<div class="quote-confirm-next"><span class="quote-confirm-step" aria-hidden="true">01</span><div><strong>Next, a quick call</strong><span>We\'ll discuss your property and find a convenient time to visit.</span></div></div>',
                        footer: '<i class="bi bi-shield-check" aria-hidden="true"></i> Free site survey &middot; No obligation',
                        didOpen: function (popup) {
                            var name = (data.name || '').trim();
                            popup.querySelector('.quote-confirm-greeting').textContent = name ? 'Thank you, ' + name + '.' : 'Thank you for choosing Eyetrack.';
                        },
                        showCancelButton: true,
                        confirmButtonText: '<i class="bi bi-whatsapp me-2" aria-hidden="true"></i>Continue on WhatsApp',
                        cancelButtonText: 'Done',
                        buttonsStyling: false,
                        focusCancel: true,
                        customClass: {
                            container: 'quote-confirm-backdrop',
                            popup: 'quote-confirmation',
                            confirmButton: 'quote-confirm-action quote-confirm-whatsapp',
                            cancelButton: 'quote-confirm-action quote-confirm-done'
                        }
                    }).then(function (res) {
                        if (res.isConfirmed) window.open(data.whatsapp_url, '_blank', 'noopener');
                    });
                } else {
                    alert('Thanks ' + data.name + '! ' + text);
                }
            }).catch(function () {
                // Fall back to a normal form post so the lead is never lost.
                btn.disabled = false;
                form.submit();
            });
        });
    });
})();
