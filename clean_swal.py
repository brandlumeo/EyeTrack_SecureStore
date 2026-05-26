import codecs
import re

def clean_file(path):
    text = codecs.open(path, 'r', 'utf-8').read()
    
    # Remove CSS
    text = re.sub(r'<!-- SweetAlert2 Premium Styles -->.*?</style>', '', text, flags=re.DOTALL)
    
    # Remove JS
    text = re.sub(r'<!-- SweetAlert2 Scripts -->.*?</script>', '', text, flags=re.DOTALL)
    
    # Also catch script start and script end logic for base_premium / base
    text = re.sub(r'<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11[^>]*></script>\s*<script>\s*document.addEventListener\(\'DOMContentLoaded\', function\(\).*?\}\s*\)\;\s*\}\s*\)\;\s*\}\s*\)\;\s*\}\s*\)\;\s*\}\s*\)\;\s*\)\;\s*\}\s*\)\;\s*\)\;\s*\)\;\s*\)\;\s*\}\)\;\s*</script>', '', text, flags=re.DOTALL) # Just an attempt

    # Since regex is risky with DOTALL across a whole file if there are multiple script tags, I will use a stricter search
    start_str_css = "<!-- SweetAlert2 Premium Styles -->"
    end_str_css = "</style>"
    
    while start_str_css in text:
        start_idx = text.find(start_str_css)
        end_idx = text.find(end_str_css, start_idx) + len(end_str_css)
        if start_idx != -1 and text.find(end_str_css, start_idx) != -1:
            text = text[:start_idx] + text[end_idx:]
        else: break

    start_str_js = "<!-- SweetAlert2 Scripts -->"
    end_str_js = "</script>\n"
    # Wait, there are two script tags. The second script tag ends with </script>. We will search for 'document.querySelectorAll'
    while start_str_js in text:
        start_idx = text.find(start_str_js)
        # find the second </script> after start_idx
        first_end = text.find("</script>", start_idx)
        second_end = text.find("</script>", first_end + 9)
        if second_end != -1:
            text = text[:start_idx] + text[second_end + 9:]
        else: break
        
    codecs.open(path, 'w', 'utf-8').write(text)
    print("Cleaned up", path)

clean_file(r'templates\admin_dashboard\base.html')
clean_file(r'templates\admin_dashboard\base_premium.html')
