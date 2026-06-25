/* ============================================================
   CDMS Viewport — Client Application
   Vanilla JS. No build step. No dependencies.
   ============================================================ */

(function () {
    'use strict';

    // ---- State ----------------------------------------------------------- //
    const state = {
        currentTab: 'overview',
        stats: null,
        timelinePaused: false,
        timelineBuffer: [],
        sseConnected: false,
    };

    // ---- DOM Helpers ----------------------------------------------------- //
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    function el(tag, attrs = {}, children = []) {
        const node = document.createElement(tag);
        for (const [k, v] of Object.entries(attrs)) {
            if (k === 'class') node.className = v;
            else if (k === 'text') node.textContent = v;
            else if (k === 'html') node.innerHTML = v;
            else if (k.startsWith('on') && typeof v === 'function') {
                node.addEventListener(k.slice(2).toLowerCase(), v);
            } else if (v !== null && v !== undefined) {
                node.setAttribute(k, v);
            }
        }
        for (const c of [].concat(children)) {
            if (c == null) continue;
            node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
        }
        return node;
    }

    // ---- API ------------------------------------------------------------- //
    async function api(path, params = {}) {
        const qs = new URLSearchParams();
        for (const [k, v] of Object.entries(params)) {
            if (v != null && v !== '') qs.set(k, v);
        }
        const url = `/api/${path}${qs.toString() ? '?' + qs.toString() : ''}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`);
        return res.json();
    }

    // ---- Relative Time --------------------------------------------------- //
    function relTime(iso) {
        if (!iso) return '—';
        const d = new Date(iso);
        const now = Date.now();
        const diff = now - d.getTime();
        const s = Math.floor(diff / 1000);
        if (s < 60) return `${s}s ago`;
        const m = Math.floor(s / 60);
        if (m < 60) return `${m}m ago`;
        const h = Math.floor(m / 60);
        if (h < 24) return `${h}h ago`;
        const day = Math.floor(h / 24);
        if (day < 30) return `${day}d ago`;
        return d.toLocaleDateString();
    }

    // ---- Valence --------------------------------------------------------- //
    function valenceClass(v) {
        if (v > 0.15) return 'positive';
        if (v < -0.15) return 'negative';
        return 'neutral';
    }

    // ---- Tab Navigation -------------------------------------------------- //
    function initTabs() {
        $$('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const tab = link.dataset.tab;
                switchTab(tab);
            });
        });
    }

    function switchTab(tab) {
        state.currentTab = tab;
        $$('.nav-link').forEach(l => l.classList.toggle('active', l.dataset.tab === tab));
        $$('.tab-panel').forEach(p => p.classList.toggle('active', p.id === `panel-${tab}`));

        // Lazy-load tab content
        switch (tab) {
            case 'overview': loadOverview(); loadFilterOptions(); break;
            case 'timeline': loadTimeline(); break;
            case 'persona': loadPersona(); break;
            case 'scars': loadScars(); break;
            case 'temperament': loadTemperament(); break;
        }
    }

    // ---- Sidebar Stats --------------------------------------------------- //
    function updateSidebarStats(stats) {
        if (!stats) return;
        $('#stat-episodic').textContent = stats.episodic ?? '—';
        $('#stat-gist').textContent = stats.gist ?? '—';
        $('#stat-scars').textContent = stats.scars ?? '—';
        $('#stat-edges').textContent = stats.support_edges ?? '—';
        $('#sidebar-archetype').textContent = stats.archetype ?? '—';
    }

    // ---- Overview -------------------------------------------------------- //
    async function loadOverview() {
        try {
            const stats = await api('stats');
            state.stats = stats;
            updateSidebarStats(stats);

            $('#overview-episodic').textContent = stats.episodic ?? 0;
            $('#overview-gist').textContent = stats.gist ?? 0;
            $('#overview-scars').textContent = stats.scars ?? 0;
            $('#overview-edges').textContent = stats.support_edges ?? 0;

            // Health signals
            const health = $('#overview-health');
            health.innerHTML = '';
            const nullRate = stats.affect_null_rate;
            const nullDisplay = nullRate !== null
                ? `${(nullRate * 100).toFixed(0)}%`
                : '—';
            health.appendChild(healthItem('Affect null rate', nullDisplay, nullRate > 0.5 ? 'warn' : 'ok'));
            health.appendChild(healthItem('Consolidations skipped', stats.consolidations_skipped ?? 0, stats.consolidations_skipped > 0 ? 'warn' : 'ok'));
            if (stats.quarantined_at) {
                health.appendChild(healthItem('Store reset', `yes — ${relTime(stats.quarantined_at)}`, 'warn'));
            }

            // Recent timeline
            const timeline = await api('timeline', { limit: 5 });
            const container = $('#overview-timeline');
            container.innerHTML = '';
            if (!timeline.length) {
                container.appendChild(el('div', { class: 'empty-state', text: 'No episodes yet' }));
            } else {
                timeline.forEach(ep => container.appendChild(compactEpisode(ep)));
            }
        } catch (err) {
            console.error('Overview load failed:', err);
        }
    }

    function healthItem(label, value, status) {
        return el('div', { class: 'health-item' }, [
            el('span', { class: 'health-label', text: label }),
            el('span', { class: `health-value ${status}`, text: String(value) }),
        ]);
    }

    function compactEpisode(ep) {
        return el('div', { class: 'compact-item' }, [
            el('span', { class: `valence-dot ${valenceClass(ep.valence)}` }),
            el('span', { class: 'salience-bar' }, [
                el('span', { class: 'salience-bar-fill', style: `width:${Math.min(100, ep.base_salience * 20)}%` }),
            ]),
            el('span', { class: 'compact-item-text', text: ep.trigger_prompt || '(empty)' }),
            el('span', { class: 'compact-item-meta' }, [
                el('span', { class: `badge ${ep.provenance || 'trusted'}`, text: ep.provenance || 'trusted' }),
                el('span', { text: relTime(ep.timestamp) }),
            ]),
        ]);
    }

    // ---- Timeline -------------------------------------------------------- //
    async function loadTimeline() {
        try {
            const project = $('#timeline-project')?.value || '';
            const params = { limit: 50 };
            if (project) params.project = project;
            const episodes = await api('timeline', params);
            const container = $('#timeline-feed');
            container.innerHTML = '';
            if (!episodes.length) {
                container.appendChild(el('div', { class: 'empty-state', text: 'No episodes yet' }));
                return;
            }
            episodes.forEach(ep => container.appendChild(episodeCard(ep)));
        } catch (err) {
            console.error('Timeline load failed:', err);
        }
    }

    function episodeCard(ep, isNew = false) {
        const card = el('div', { class: `episode-card${isNew ? ' new' : ''}` }, [
            el('div', { class: 'episode-header' }, [
                el('span', { class: `valence-dot ${valenceClass(ep.valence)}` }),
                el('span', { class: 'salience-bar' }, [
                    el('span', { class: 'salience-bar-fill', style: `width:${Math.min(100, ep.base_salience * 20)}%` }),
                ]),
                el('span', { text: relTime(ep.timestamp) }),
                ep.project ? el('span', { class: 'badge', text: ep.project }) : null,
                el('span', { class: `badge ${ep.provenance || 'trusted'}`, text: ep.provenance || 'trusted' }),
            ]),
            el('div', { class: 'episode-body' }, [
                el('div', { class: 'episode-field' }, [
                    el('div', { class: 'episode-field-label', text: 'Trigger' }),
                    el('div', { class: 'episode-field-value', text: ep.trigger_prompt || '—' }),
                ]),
                el('div', { class: 'episode-field' }, [
                    el('div', { class: 'episode-field-label', text: 'Action' }),
                    el('div', { class: 'episode-field-value', text: ep.action_taken || '—' }),
                ]),
            ]),
            el('div', { class: 'episode-footer' }, [
                el('span', { text: `S0: ${ep.base_salience?.toFixed(2) ?? '—'}` }),
                el('span', { text: `val: ${ep.valence?.toFixed(2) ?? '—'}` }),
                el('span', { text: `seen: ${ep.access_count ?? 0}` }),
                ep.session_id ? el('span', { text: `session: ${ep.session_id.substring(0, 8)}` }) : null,
            ]),
        ]);
        return card;
    }

    // ---- Persona --------------------------------------------------------- //
    async function loadPersona() {
        try {
            const [paths, gists] = await Promise.all([
                api('paths'),
                api('persona'),
            ]);

            // Paths
            const pathsContainer = $('#persona-paths');
            pathsContainer.innerHTML = '';
            if (!paths.length) {
                pathsContainer.appendChild(el('div', { class: 'empty-state', text: 'No persona paths yet' }));
            } else {
                paths.forEach(p => {
                    pathsContainer.appendChild(el('div', { class: 'path-item' }, [
                        el('span', { class: 'path-subject', text: p.subject }),
                        el('span', { class: 'path-relation', text: p.relation }),
                        el('span', { class: 'path-object', text: p.object }),
                        el('span', { class: 'path-support', text: p.support }),
                    ]));
                });
            }

            // Gists
            const gistsContainer = $('#persona-gists');
            gistsContainer.innerHTML = '';
            if (!gists.length) {
                gistsContainer.appendChild(el('div', { class: 'empty-state', text: 'No gists yet' }));
            } else {
                gists.forEach(g => {
                    gistsContainer.appendChild(el('div', { class: 'gist-item' }, [
                        el('div', { class: 'gist-sro' }, [
                            el('span', { class: 'gist-sro-subject', text: g.subject }),
                            el('span', { class: 'gist-sro-relation', text: ` ${g.relation} ` }),
                            el('span', { class: 'gist-sro-object', text: g.object }),
                        ]),
                        g.exemplar ? el('div', { class: 'gist-exemplar', text: g.exemplar }) : null,
                        el('div', { class: 'gist-meta' }, [
                            el('span', { text: `val: ${g.valence?.toFixed(2)}` }),
                            el('span', { text: `support: ${g.support_count}` }),
                            el('span', { text: `freq: ${g.frequency}` }),
                            el('span', { text: `cycles: ${g.survived_cycles}` }),
                        ]),
                    ]));
                });
            }
        } catch (err) {
            console.error('Persona load failed:', err);
        }
    }

    // ---- Scars ----------------------------------------------------------- //
    async function loadScars() {
        try {
            const scars = await api('scars');
            const container = $('#scars-list');
            container.innerHTML = '';
            if (!scars.length) {
                container.appendChild(el('div', { class: 'scar-empty' }, [
                    el('p', { text: 'No guardrails yet.' }),
                    el('p', { style: 'margin-top:0.5rem;font-size:0.75rem', text: 'The agent hasn\'t hit a wall.' }),
                ]));
                return;
            }
            scars.forEach(s => {
                container.appendChild(el('div', { class: 'scar-card' }, [
                    el('div', { class: 'scar-header' }, [
                        el('span', { class: `badge ${s.origin === 'pinned' ? 'pinned' : 'elevated'}`, text: s.origin }),
                        el('span', { class: 'badge', text: s.project || 'global' }),
                    ]),
                    el('div', { class: 'scar-trigger', text: s.crisis_trigger }),
                    el('div', { class: 'scar-rule', text: s.remediation_rule }),
                    el('div', { class: 'scar-meta' }, [
                        el('span', { text: relTime(s.timestamp) }),
                    ]),
                ]));
            });
        } catch (err) {
            console.error('Scars load failed:', err);
        }
    }

    // ---- Temperament ----------------------------------------------------- //
    async function loadTemperament() {
        try {
            const data = await api('temperament');
            // Dials
            const dialsContainer = $('#temp-dials');
            dialsContainer.innerHTML = '';
            data.dials.forEach(d => {
                const range = d.upper - d.lower;
                const seedPct = d.seed * 100;
                const currentPct = d.current * 100;
                const lowerPct = d.lower * 100;
                const upperPct = d.upper * 100;
                dialsContainer.appendChild(el('div', { class: 'dial-item' }, [
                    el('span', { class: 'dial-name', text: d.name }),
                    el('span', { class: 'dial-values', text: `seed ${d.seed.toFixed(2)} → current ${d.current.toFixed(2)}` }),
                    el('div', { class: 'dial-bar-container' }, [
                        el('div', { class: 'dial-bar-bg' }),
                        el('div', { class: 'dial-bar-bounds', style: `left:${lowerPct}%;width:${upperPct - lowerPct}%` }),
                        el('div', { class: 'dial-bar-seed', style: `left:${seedPct}%` }),
                        el('div', { class: 'dial-bar-current', style: `left:${currentPct}%` }),
                    ]),
                ]));
            });

            // Radar chart
            renderRadar(data.dials);
        } catch (err) {
            console.error('Temperament load failed:', err);
        }
    }

    function renderRadar(dials) {
        const svg = $('#radar-svg');
        svg.innerHTML = '';
        const cx = 150, cy = 150, r = 110;
        const n = dials.length;
        if (n === 0) return;

        // Grid rings
        for (let i = 1; i <= 4; i++) {
            const ringR = (r / 4) * i;
            const points = [];
            for (let j = 0; j < n; j++) {
                const angle = (Math.PI * 2 * j) / n - Math.PI / 2;
                points.push(`${cx + ringR * Math.cos(angle)},${cy + ringR * Math.sin(angle)}`);
            }
            const polygon = el('polygon', {
                points: points.join(' '),
                fill: 'none',
                stroke: 'var(--border)',
                'stroke-width': '0.5',
            });
            svg.appendChild(polygon);
        }

        // Axis lines
        for (let j = 0; j < n; j++) {
            const angle = (Math.PI * 2 * j) / n - Math.PI / 2;
            const line = el('line', {
                x1: cx, y1: cy,
                x2: cx + r * Math.cos(angle),
                y2: cy + r * Math.sin(angle),
                stroke: 'var(--border)',
                'stroke-width': '0.5',
            });
            svg.appendChild(line);
        }

        // Seed polygon (faint)
        const seedPoints = dials.map((d, j) => {
            const angle = (Math.PI * 2 * j) / n - Math.PI / 2;
            const dist = d.seed * r;
            return `${cx + dist * Math.cos(angle)},${cy + dist * Math.sin(angle)}`;
        }).join(' ');
        svg.appendChild(el('polygon', {
            points: seedPoints,
            fill: 'none',
            stroke: 'var(--text-dim)',
            'stroke-width': '1',
            'stroke-dasharray': '3,3',
        }));

        // Current polygon (solid)
        const currentPoints = dials.map((d, j) => {
            const angle = (Math.PI * 2 * j) / n - Math.PI / 2;
            const dist = d.current * r;
            return `${cx + dist * Math.cos(angle)},${cy + dist * Math.sin(angle)}`;
        }).join(' ');
        svg.appendChild(el('polygon', {
            points: currentPoints,
            fill: 'rgba(196,167,125,0.12)',
            stroke: 'var(--accent)',
            'stroke-width': '1.5',
        }));

        // Current dots + labels
        dials.forEach((d, j) => {
            const angle = (Math.PI * 2 * j) / n - Math.PI / 2;
            const dist = d.current * r;
            const x = cx + dist * Math.cos(angle);
            const y = cy + dist * Math.sin(angle);
            svg.appendChild(el('circle', {
                cx: x, cy: y, r: 3,
                fill: 'var(--accent)',
            }));
            // Label
            const labelR = r + 18;
            const lx = cx + labelR * Math.cos(angle);
            const ly = cy + labelR * Math.sin(angle);
            const label = el('text', {
                x: lx, y: ly,
                'text-anchor': 'middle',
                'dominant-baseline': 'middle',
                fill: 'var(--text-dim)',
                'font-size': '9',
                'font-family': 'var(--font)',
            });
            label.textContent = d.name.replace(/_/g, ' ');
            svg.appendChild(label);
        });
    }

    // ---- Search ---------------------------------------------------------- //
    function initSearch() {
        const input = $('#search-input');
        const btn = $('#search-btn');
        const trigger = () => performSearch(input.value);
        btn.addEventListener('click', trigger);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') trigger();
        });
    }

    async function performSearch(query) {
        if (!query.trim()) return;
        const tiers = Array.from($$('.search-tiers input:checked')).map(i => i.value).join(',');
        const results = await api('search', { q: query, tiers, top_k: 12 });
        const container = $('#search-results');
        container.innerHTML = '';
        if (!results.length) {
            container.appendChild(el('div', { class: 'empty-state', text: 'No results' }));
            return;
        }
        results.forEach(r => {
            container.appendChild(el('div', { class: 'result-card' }, [
                el('div', { class: 'result-header' }, [
                    el('span', { class: 'result-tier', text: r.tier }),
                    el('span', { class: 'result-score', text: `score ${r.score}` }),
                ]),
                el('div', { class: 'result-text', text: r.text }),
            ]));
        });
    }

    // ---- SSE (Live Feed) ------------------------------------------------- //
    function initSSE() {
        const indicator = $('#live-indicator');
        const dot = indicator.querySelector('.live-dot');
        const text = indicator.querySelector('.live-text');

        function connect() {
            const es = new EventSource('/api/sse');

            es.addEventListener('connected', () => {
                state.sseConnected = true;
                indicator.classList.add('connected');
                indicator.classList.remove('paused');
                text.textContent = 'live';
            });

            es.addEventListener('episode', (e) => {
                const ep = JSON.parse(e.data);

                // Buffer if paused
                if (state.timelinePaused) {
                    state.timelineBuffer.push(ep);
                    // Update pause button to show count
                    const btn = $('#timeline-pause');
                    if (btn) {
                        btn.textContent = `Resume live (${state.timelineBuffer.length} new)`;
                    }
                    return;
                }

                // Prepend to timeline if visible
                if (state.currentTab === 'timeline') {
                    const container = $('#timeline-feed');
                    const card = episodeCard(ep, true);
                    container.insertBefore(card, container.firstChild);
                    // Keep max 200 in DOM
                    while (container.children.length > 200) {
                        container.removeChild(container.lastChild);
                    }
                }
                // Update sidebar stats optimistically
                if (state.stats) {
                    state.stats.episodic = (state.stats.episodic || 0) + 1;
                    updateSidebarStats(state.stats);
                }
            });

            es.addEventListener('gist', (e) => {
                // Refresh persona tab if visible
                if (state.currentTab === 'persona') {
                    loadPersona();
                }
                // Update sidebar gist count
                if (state.stats) {
                    state.stats.gist = (state.stats.gist || 0) + 1;
                    updateSidebarStats(state.stats);
                }
            });

            es.addEventListener('scar', (e) => {
                // Refresh scars tab if visible
                if (state.currentTab === 'scars') {
                    loadScars();
                }
                if (state.stats) {
                    state.stats.scars = (state.stats.scars || 0) + 1;
                    updateSidebarStats(state.stats);
                }
            });

            es.onerror = () => {
                state.sseConnected = false;
                indicator.classList.remove('connected');
                text.textContent = 'reconnecting';
                es.close();
                setTimeout(connect, 3000);
            };
        }

        connect();
    }

    // ---- Timeline Pause -------------------------------------------------- //
    function initTimelineControls() {
        const btn = $('#timeline-pause');
        if (!btn) return;
        btn.addEventListener('click', () => {
            state.timelinePaused = !state.timelinePaused;
            btn.textContent = state.timelinePaused ? 'Resume live' : 'Pause live';
            if (state.timelinePaused) {
                $('#live-indicator').classList.add('paused');
            } else {
                $('#live-indicator').classList.remove('paused');
                // Flush buffered events
                if (state.timelineBuffer.length && state.currentTab === 'timeline') {
                    const container = $('#timeline-feed');
                    state.timelineBuffer.forEach(ep => {
                        const card = episodeCard(ep, true);
                        container.insertBefore(card, container.firstChild);
                    });
                    // Trim to 200
                    while (container.children.length > 200) {
                        container.removeChild(container.lastChild);
                    }
                    state.timelineBuffer = [];
                }
            }
        });
    }

    // ---- Filter Dropdowns ------------------------------------------------ //
    function initFilterControls() {
        const projSelect = $('#timeline-project');
        if (projSelect) {
            projSelect.addEventListener('change', () => {
                if (state.currentTab === 'timeline') loadTimeline();
            });
        }
    }

    async function loadFilterOptions() {
        try {
            const [projects, sessions] = await Promise.all([
                api('projects'),
                api('sessions'),
            ]);

            // Timeline project filter
            const projSelect = $('#timeline-project');
            if (projSelect) {
                projSelect.innerHTML = '<option value="">All projects</option>';
                projects.forEach(p => {
                    const opt = el('option', { value: p, text: p.length > 40 ? p.substring(0, 40) + '…' : p });
                    projSelect.appendChild(opt);
                });
            }

            // Timeline session filter (reuse the project select area for now — can be extended)
            // Store sessions for potential future use
            state.sessions = sessions;
        } catch (e) {
            console.error('Filter load failed:', e);
        }
    }

    // ---- Init ------------------------------------------------------------ //
    async function init() {
        initTabs();
        initSearch();
        initTimelineControls();
        initFilterControls();
        initSSE();
        loadFilterOptions();

        // Load initial tab
        await loadOverview();

        // Periodic stats refresh (every 10s as fallback if SSE is down)
        setInterval(async () => {
            if (!state.sseConnected) {
                try {
                    const stats = await api('stats');
                    state.stats = stats;
                    updateSidebarStats(stats);
                } catch (e) { /* ignore */ }
            }
        }, 10000);

        // Refresh filter options periodically (new projects/sessions appear)
        setInterval(loadFilterOptions, 60000);
    }

    document.addEventListener('DOMContentLoaded', init);
})();
