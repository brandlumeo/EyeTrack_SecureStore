/* Storage calculator page: counters, slider read-outs, an instant estimate and the result meter.
   tools.js still sends every change to the storage API and writes the server's figures into the same
   [data-out] fields; the instant estimate here only removes the wait for that round trip. */
(function () {
    'use strict';

    var form = document.querySelector('[data-st-form]');
    if (!form) return;
    var configEl = document.getElementById('st-config');
    var config = configEl ? JSON.parse(configEl.textContent) : null;

    function field(name) { return form.elements[name]; }
    function value(name) {
        var el = field(name);
        if (!el) return null;
        if (el.length !== undefined && el.tagName !== 'SELECT' && el.tagName !== 'INPUT') {
            for (var i = 0; i < el.length; i++) if (el[i].checked) return el[i].value;
            return null;
        }
        return el.value;
    }
    function setOut(key, text) {
        document.querySelectorAll('[data-out="' + key + '"]').forEach(function (el) { el.textContent = text; });
    }
    // Same rounding as Python's round() for these values; the API result replaces it moments later anyway.
    function round(x, digits) { return Number(Math.round(Number(x + 'e' + digits)) + 'e-' + digits); }

    /* ---- +/- camera counter ---- */
    form.querySelectorAll('[data-st-step]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var input = field('cameras');
            var next = (parseInt(input.value, 10) || 0) + Number(btn.getAttribute('data-st-step'));
            input.value = Math.min(Number(input.max) || 128, Math.max(Number(input.min) || 1, next));
            input.dispatchEvent(new Event('input', { bubbles: true }));
        });
    });

    /* ---- slider read-outs and the motion-only field ---- */
    var activity = form.querySelector('[data-st-activity]');
    function syncControls() {
        var hours = form.querySelector('[data-st-out="hours"]');
        var act = form.querySelector('[data-st-out="activity"]');
        if (hours) hours.textContent = value('hours') + ' h';
        if (act) act.textContent = value('activity') + '%';
        if (activity) activity.hidden = value('mode') !== 'motion';
    }

    /* ---- instant estimate (mirrors store.tools.storage_estimate) ---- */
    function inRange(v, min, max) { return Number.isFinite(v) && v >= min && v <= max; }
    function estimate() {
        if (!config) return;
        var cameras = Number(value('cameras')), hours = Number(value('hours')), act = Number(value('activity'));
        var days = Number(value('days')), fps = Number(value('fps'));
        var codec = value('codec'), resolution = value('resolution');
        if (!Number.isInteger(cameras) || !inRange(cameras, 1, 128) || !inRange(hours, 1, 24) || !inRange(act, 5, 100)) return;
        var table = config.bitrates[codec];
        if (!table || table[resolution] === undefined || !days || !fps) return;

        var activityPct = value('mode') === 'motion' ? act : 100;
        var factor = (hours / 24) * (activityPct / 100);
        var mbps = table[resolution] * fps / 25;
        var gbPerDay = mbps * 86400 / 8 / 1000 * factor;
        var totalGb = gbPerDay * days * cameras;
        var totalTb = totalGb / 1000;

        var needed = totalTb * config.headroom, drives = 1, size = null;
        for (var i = 0; i < config.hdd_sizes.length; i++) {
            if (config.hdd_sizes[i] >= needed) { size = config.hdd_sizes[i]; break; }
        }
        if (size === null) {
            size = config.hdd_sizes[config.hdd_sizes.length - 1];
            drives = Math.ceil(needed / size);
        }

        setOut('hdd', drives + ' × ' + size + ' TB');
        setOut('total_tb', round(totalTb, 2));
        setOut('days', days);
        setOut('bandwidth_mbps', round(mbps * cameras, 1));
        setOut('total_gb', round(totalGb, 1));
        setOut('mbps_each', round(mbps, 2));
        setOut('gb_per_day_each', round(gbPerDay, 1));
        var err = form.querySelector('[data-calc-error]');
        if (err) err.classList.add('d-none');
    }

    /* ---- disk-usage meter, redrawn whenever the figures change (from either source) ---- */
    var result = document.getElementById('st-result');
    var fill = result && result.querySelector('[data-st-meter-fill]');
    var label = result && result.querySelector('[data-st-meter-label]');
    function drawMeter() {
        if (!fill) return;
        var hddText = (result.querySelector('[data-out="hdd"]') || {}).textContent || '';
        var tb = parseFloat((result.querySelector('[data-out="total_tb"]') || {}).textContent);
        var m = hddText.match(/(\d+)\s*×\s*(\d+(?:\.\d+)?)/);
        if (!m || !Number.isFinite(tb)) return;
        var drives = Number(m[1]), size = Number(m[2]), capacity = drives * size;
        var pct = Math.min(100, Math.max(2, tb / capacity * 100));
        var width = pct.toFixed(1) + '%';
        var text = tb + ' TB of footage on ' + (drives > 1 ? drives + ' drives (' + capacity + ' TB)' : 'a ' + size + ' TB drive') +
            ' · ' + Math.round(tb / capacity * 100) + '% used';
        if (fill.style.width !== width) fill.style.width = width;
        if (label.textContent !== text) label.textContent = text;
    }
    // Watch only the two figures the meter reads (never the meter itself, or it would trigger itself).
    if (result && window.MutationObserver) {
        var watcher = new MutationObserver(drawMeter);
        result.querySelectorAll('[data-out="hdd"], [data-out="total_tb"]').forEach(function (el) {
            watcher.observe(el, { childList: true, characterData: true, subtree: true });
        });
    }

    form.addEventListener('input', function () { syncControls(); estimate(); });
    form.addEventListener('change', function () { syncControls(); estimate(); });
    syncControls();
    drawMeter();

    /* ---- mobile result bar: visible while editing the form with the result off-screen ---- */
    var mini = document.querySelector('[data-st-mini]');
    if (mini && result && 'IntersectionObserver' in window) {
        var formVisible = false, resultVisible = true;
        var update = function () { mini.classList.toggle('is-visible', formVisible && !resultVisible); };
        new IntersectionObserver(function (entries) {
            entries.forEach(function (e) {
                if (e.target === form) formVisible = e.isIntersecting;
                else resultVisible = e.isIntersecting;
            });
            update();
        }, { threshold: 0.08 }).observe(form);
        new IntersectionObserver(function (entries) {
            resultVisible = entries[0].isIntersecting;
            update();
        }, { threshold: 0.25 }).observe(result);
        mini.addEventListener('click', function (e) {
            e.preventDefault();
            result.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    }
})();
