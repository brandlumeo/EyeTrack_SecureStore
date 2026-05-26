import codecs

def inject():
    text = codecs.open(r'templates\base.html', 'r', 'utf-8').read()
    css_injection = """
    <!-- SweetAlert2 Premium Styles -->
    <link href="https://cdn.jsdelivr.net/npm/sweetalert2@11.7.3/dist/sweetalert2.min.css" rel="stylesheet">
    <style>
        .swal-glass-popup { background: rgba(15, 23, 42, 0.95) !important; backdrop-filter: blur(16px) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; border-radius: 1.5rem !important; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7) !important; color: #f8fafc !important; font-family: 'Inter', sans-serif !important; }
        .swal-glass-title { color: #fff !important; font-weight: 700 !important; font-family: 'Outfit', sans-serif !important; font-size: 1.75rem !important; }
        .swal-btn-confirm { background: linear-gradient(135deg, #ef4444, #b91c1c) !important; border: none !important; border-radius: 0.75rem !important; font-weight: 600 !important; padding: 0.7rem 1.5rem !important; box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3) !important; color: white !important;}
        .swal-btn-cancel { background: rgba(255, 255, 255, 0.05) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; color: #94a3b8 !important; border-radius: 0.75rem !important; font-weight: 500 !important; padding: 0.7rem 1.5rem !important; margin-left: 10px; }
        .swal-btn-cancel:hover { background: rgba(255, 255, 255, 0.1) !important; color: #fff !important; }
    </style>
"""
    js_injection = """
    <!-- SweetAlert2 JS -->
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        document.querySelectorAll('form[onsubmit*="confirm"]').forEach(form => {
            let originalOnsubmit = form.getAttribute('onsubmit');
            let match = originalOnsubmit.match(/confirm\\('([^']+)'\\)/) || originalOnsubmit.match(/confirm\\(\"([^\"]+)\"\\)/);
            if (match) {
                let message = match[1];
                form.removeAttribute('onsubmit');
                form.addEventListener('submit', function(e) {
                    e.preventDefault();
                    Swal.fire({
                        title: 'Confirm Action', text: message, icon: 'warning', showCancelButton: true,
                        confirmButtonText: '<i class="bi bi-trash"></i> Yes, Proceed', cancelButtonText: 'Cancel', buttonsStyling: false,
                        customClass: { popup: 'swal-glass-popup', title: 'swal-glass-title', confirmButton: 'swal-btn-confirm btn', cancelButton: 'swal-btn-cancel btn' }
                    }).then((result) => { if (result.isConfirmed) form.submit(); });
                });
            }
        });
        document.querySelectorAll('a[onclick*="confirm"]').forEach(link => {
            let originalOnclick = link.getAttribute('onclick');
            let match = originalOnclick.match(/confirm\\('([^']+)'\\)/) || originalOnclick.match(/confirm\\(\"([^\"]+)\"\\)/);
            if (match) {
                let message = match[1];
                link.removeAttribute('onclick');
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    let targetUrl = this.href;
                    Swal.fire({
                        title: 'Are you sure?', text: message, icon: 'warning', showCancelButton: true,
                        confirmButtonText: '<i class="bi bi-exclamation-triangle"></i> Yes, Proceed', cancelButtonText: 'Cancel', buttonsStyling: false,
                        customClass: { popup: 'swal-glass-popup', title: 'swal-glass-title', confirmButton: 'swal-btn-confirm btn', cancelButton: 'swal-btn-cancel btn' }
                    }).then((result) => { if (result.isConfirmed) window.location.href = targetUrl; });
                });
            }
        });
    });
    </script>
"""
    changed = False
    if 'SweetAlert2 Premium Styles' not in text:
        text = text.replace('{% block extra_head %}{% endblock %}', css_injection + '\n    {% block extra_head %}{% endblock %}')
        changed = True
    if 'SweetAlert2 JS' not in text:
        text = text.replace('{% block extra_js %}{% endblock %}', js_injection + '\n    {% block extra_js %}{% endblock %}')
        changed = True

    if changed:
        codecs.open(r'templates\base.html', 'w', 'utf-8').write(text)
        print("Successfully injected SweetAlert natively into base.html")
    else:
        print("SweetAlert already present in base.html")

inject()
