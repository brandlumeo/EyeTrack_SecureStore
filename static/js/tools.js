/* CCTV planning tools: system builder steps, counters and live calculators.
   Every page works without this file (plain GET forms); this only adds steps and live updates. */
(function () {
    'use strict';

    /* ---------- +/- counters ---------- */
    document.querySelectorAll('[data-counter]').forEach(function (counter) {
        var input = counter.querySelector('input');
        counter.querySelectorAll('[data-counter-step]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var min = Number(input.min || 0), max = Number(input.max || 999);
                var next = (parseInt(input.value, 10) || 0) + Number(btn.dataset.counterStep);
                input.value = Math.min(max, Math.max(min, next));
                input.dispatchEvent(new Event('change', { bubbles: true }));
            });
        });
    });

    /* ---------- system builder: one question at a time ---------- */
    var builder = document.querySelector('[data-builder]');
    var plan = document.getElementById('plan');
    if (builder && !plan) {
        var steps = Array.prototype.slice.call(builder.querySelectorAll('[data-step]'));
        var prev = builder.querySelector('[data-step-prev]');
        var next = builder.querySelector('[data-step-next]');
        var submit = builder.querySelector('[data-step-submit]');
        var progress = builder.querySelector('[data-builder-progress]');
        var current = 0;

        steps.forEach(function () { progress.appendChild(document.createElement('span')); });
        builder.classList.add('js-builder');

        var show = function (index) {
            current = index;
            steps.forEach(function (step, i) { step.classList.toggle('is-active', i === index); });
            Array.prototype.forEach.call(progress.children, function (bar, i) { bar.classList.toggle('done', i <= index); });
            prev.hidden = index === 0;
            next.hidden = index === steps.length - 1;
            submit.hidden = index !== steps.length - 1;
        };

        var countsValid = function () {
            var step = steps[current];
            var inputs = step.querySelectorAll('input[type="number"]');
            if (!inputs.length) return true;
            var total = 0;
            inputs.forEach(function (input) { total += parseInt(input.value, 10) || 0; });
            var msg = step.querySelector('[data-step-error]');
            if (!msg) {
                msg = document.createElement('div');
                msg.className = 'tool-error mt-2';
                msg.setAttribute('data-step-error', '');
                step.appendChild(msg);
            }
            msg.textContent = total > 0 ? '' : 'Add at least one camera point, indoor or outdoor.';
            return total > 0;
        };

        next.addEventListener('click', function () {
            if (countsValid()) show(Math.min(current + 1, steps.length - 1));
        });
        prev.addEventListener('click', function () { show(Math.max(current - 1, 0)); });
        // Picking a single-choice answer moves straight on to the next question.
        builder.addEventListener('change', function (e) {
            if (e.target.type === 'radio' && current < steps.length - 1) {
                setTimeout(function () { show(current + 1); }, 180);
            }
        });
        show(0);
    }
    if (plan && window.innerWidth < 992 && !window.location.hash) {
        plan.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    /* ---------- live calculators ---------- */
    var setOut = function (scope, key, value) {
        scope.querySelectorAll('[data-out="' + key + '"]').forEach(function (el) { el.textContent = value; });
    };

    var renderers = {
        storage: function (scope, r) {
            setOut(scope, 'hdd', r.hdd ? r.hdd.drives + ' × ' + r.hdd.size_tb + ' TB' : '-');
            ['total_tb', 'days', 'bandwidth_mbps', 'total_gb'].forEach(function (k) { setOut(scope, k, r[k]); });
            if (r.lines.length) {
                setOut(scope, 'mbps_each', r.lines[0].mbps_each);
                setOut(scope, 'gb_per_day_each', r.lines[0].gb_per_day_each);
            }
        },
        lens: function (scope, r) {
            ['focal_mm', 'fov_deg', 'pixels_per_m', 'suggestion'].forEach(function (k) { setOut(scope, k, r[k]); });
            scope.querySelectorAll('[data-out="dori"]').forEach(function (el) {
                el.textContent = r.dori.name;
                el.dataset.level = r.dori.name;
            });
            setOut(scope, 'dori_description', r.dori.description + '.');
            var rows = scope.querySelector('[data-out-rows]');
            if (rows) {
                rows.innerHTML = '';
                r.options.forEach(function (o) {
                    var tr = document.createElement('tr');
                    [o.lens_mm + ' mm', o.fov_deg + '°', o.scene_width_m + ' m wide'].forEach(function (text) {
                        var td = document.createElement('td');
                        td.textContent = text;
                        tr.appendChild(td);
                    });
                    var detail = document.createElement('td');
                    detail.textContent = o.pixels_per_m + ' px/m ';
                    var pill = document.createElement('span');
                    pill.className = 'dori-pill';
                    pill.dataset.level = o.dori;
                    pill.textContent = o.dori;
                    detail.appendChild(pill);
                    tr.appendChild(detail);
                    rows.appendChild(tr);
                });
            }
        }
    };

    document.querySelectorAll('[data-calc][data-api]').forEach(function (form) {
        var kind = form.dataset.api.indexOf('lens') !== -1 ? 'lens' : 'storage';
        var scope = form.closest('.row') || document;
        var errorBox = form.querySelector('[data-calc-error]');
        var submitBtn = form.querySelector('[data-calc-submit]');
        var timer = null, seq = 0;
        if (submitBtn) submitBtn.classList.add('d-none');

        var run = function () {
            var params = new URLSearchParams(new FormData(form)).toString();
            var mine = ++seq;
            fetch(form.dataset.api + '?' + params, { headers: { 'Accept': 'application/json' } })
                .then(function (res) { return res.json(); })
                .then(function (data) {
                    if (mine !== seq) return; // a newer request is on its way
                    if (!data.ok) {
                        var messages = [];
                        Object.keys(data.errors || {}).forEach(function (field) {
                            data.errors[field].forEach(function (err) { messages.push(err.message); });
                        });
                        errorBox.textContent = messages.join(' ');
                        errorBox.classList.remove('d-none');
                        return;
                    }
                    errorBox.classList.add('d-none');
                    renderers[kind](scope, data.result);
                    history.replaceState(null, '', form.action + '?' + params);
                })
                .catch(function () {
                    if (submitBtn) submitBtn.classList.remove('d-none'); // fall back to the normal submit
                });
        };

        form.addEventListener('input', function () {
            clearTimeout(timer);
            timer = setTimeout(run, 250);
        });
        form.addEventListener('change', function () {
            clearTimeout(timer);
            run();
        });
    });
})();
