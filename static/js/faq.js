(() => {
    const root = document.querySelector('.fq');
    if (!root) return;

    const input = document.getElementById('fqSearch');
    const countEl = document.getElementById('fqCount');
    const empty = document.getElementById('fqEmpty');
    const emptyTerm = document.getElementById('fqEmptyTerm');
    const sections = [...root.querySelectorAll('.fq-section')];
    const items = [...root.querySelectorAll('.fq-item')].map((el) => {
        const q = el.querySelector('.fq-item__text');
        const a = el.querySelector('.fq-item__a p');
        return { el, q, a, qText: q.textContent, aText: a.textContent, wasOpen: el.open };
    });
    const total = items.length;
    const links = [...root.querySelectorAll('.fq-toc__link')];
    const setActive = (id) => links.forEach((l) => l.classList.toggle('is-active', l.dataset.section === id));

    // Highlight matches without ever inserting user input as HTML.
    const highlight = (node, text, term) => {
        node.textContent = '';
        if (!term) { node.textContent = text; return; }
        const lower = text.toLowerCase();
        let from = 0;
        let at = lower.indexOf(term);
        while (at !== -1) {
            node.append(text.slice(from, at));
            const mark = document.createElement('mark');
            mark.textContent = text.slice(at, at + term.length);
            node.append(mark);
            from = at + term.length;
            at = lower.indexOf(term, from);
        }
        node.append(text.slice(from));
    };

    const filter = () => {
        const term = input.value.trim().toLowerCase();
        let shown = 0;
        items.forEach((item) => {
            const hit = !term || item.qText.toLowerCase().includes(term) || item.aText.toLowerCase().includes(term);
            item.el.hidden = !hit;
            highlight(item.q, item.qText, hit ? term : '');
            highlight(item.a, item.aText, hit ? term : '');
            // Open matching answers while searching; restore when the search is cleared.
            item.el.open = term ? hit && item.aText.toLowerCase().includes(term) : item.wasOpen;
            if (hit) shown += 1;
        });
        sections.forEach((s) => {
            const matches = s.querySelectorAll('.fq-item:not([hidden])').length;
            const count = s.querySelector('.fq-section__count');
            const all = Number(count.dataset.total);
            s.hidden = matches === 0;
            count.textContent = term ? `${matches} of ${all}` : `${all} question${all === 1 ? '' : 's'}`;
            const link = links.find((l) => l.dataset.section === s.id);
            if (link) link.classList.toggle('is-dim', matches === 0);
        });
        countEl.textContent = term ? `${shown} of ${total} answers` : `${total} answers`;
        empty.hidden = shown > 0;
        emptyTerm.textContent = input.value.trim();
        const firstVisible = sections.find((s) => !s.hidden);
        if (firstVisible) setActive(firstVisible.id);
    };

    // Remember which cards the visitor opened themselves.
    items.forEach((item) => item.el.addEventListener('toggle', () => {
        if (!input.value.trim()) item.wasOpen = item.el.open;
    }));
    input.addEventListener('input', filter);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') { input.value = ''; filter(); }
    });

    // Highlight the section being read in the side navigation.
    if ('IntersectionObserver' in window && links.length) {
        const visible = new Map();
        const io = new IntersectionObserver((entries) => {
            entries.forEach((e) => visible.set(e.target.id, e.isIntersecting ? e.boundingClientRect.top : null));
            const current = [...visible.entries()].filter(([, top]) => top !== null).sort((a, b) => a[1] - b[1])[0];
            if (current) setActive(current[0]);
        }, { rootMargin: '-110px 0px -55% 0px' });
        sections.forEach((s) => io.observe(s));
        setActive(sections[0] && sections[0].id);
    }
})();
