"""Build a standalone HTML copy of the dashboard: the same page, its data embedded, and a small stand-in
for the dashboard host's `dash` API, styled in Board UI's look. Run after `nil dashboard-data`:

    python dashboard/build_html.py OUT.html
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data" / "dashboard"
DATASETS = ["cohorts", "curves", "releases", "validation", "rosters"]
DEFAULT_PARAMS = {"cohort": "A4", "cut": "A4", "gender": "men", "nil": 40000, "position": "Linebacker",
                  "report": "revenue_share", "rs": 150000, "sport": "Football"}

HEAD = """<title>College Athlete Pay Benchmarks</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap">
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
<style>
/* Board UI: white ground, #f7f7f7 flat cards with white inner panels, neutral text, blue accent,
   its chart palette, Inter. Dark: #121212 ground, near-black cards, lighter series. */
:root {
  --color-bg: #ffffff; --color-fg: #0a0a0a; --color-fg-muted: #6b6b6b; --cds-text-secondary: #6b6b6b;
  --color-panel: #f7f7f7; --pb-inner: #ffffff; --color-border-line: #ebebeb;
  --cds-surface-popover: #ffffff; --cds-border: #ebebeb;
  --cds-chart-grid: #ebebeb; --cds-chart-axis: #d4d4d4; --cds-chart-reference: #a1a1a1; --cds-chart-muted: #d4d4d4;
  --cds-chart-categorical-1: #155dfc; --cds-chart-categorical-2: #f6339a; --cds-chart-categorical-3: #00bba7; --cds-chart-categorical-4: #ad46ff;
  --cds-chart-categorical-5: #f0b100; --cds-chart-categorical-6: #00a6f4; --cds-chart-categorical-7: #7ccf00; --cds-chart-categorical-8: #615fff;
  --pb-shadow-xs: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --cds-shadow-popover: 0 1px 1px 0 rgb(0 0 0 / 0.04), 0 4px 12px 0 rgb(0 0 0 / 0.08);
  --font-anthropic-sans: "Inter", ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --font-anthropic-serif: "Inter", ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --cds-font-size-caption: 12px; --cds-font-size-body: 14px; --cds-font-size-heading: 16px; --cds-font-size-title: 24px;
  --cds-gap-md: 16px; --cds-gap-lg: 24px; --cds-radius: 12px; --cds-dur-slow: 300ms;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --color-bg: #121212; --color-fg: #fafafa; --color-fg-muted: #a1a1a1; --cds-text-secondary: #a1a1a1;
    --color-panel: #1a1a1a; --pb-inner: #242424; --color-border-line: #2e2e2e;
    --cds-surface-popover: #262626; --cds-border: #404040;
    --cds-chart-grid: #2a2a2a; --cds-chart-axis: #404040; --cds-chart-reference: #737373; --cds-chart-muted: #404040;
    --cds-chart-categorical-1: #3392ff; --cds-chart-categorical-2: #fb64b6; --cds-chart-categorical-3: #00d5be; --cds-chart-categorical-4: #c27aff;
    --cds-chart-categorical-5: #fdc700; --cds-chart-categorical-6: #00bcff; --cds-chart-categorical-7: #9ae600; --cds-chart-categorical-8: #7c86ff;
    --pb-shadow-xs: 0 1px 2px 0 rgb(0 0 0 / 0.3); --cds-shadow-popover: 0 4px 16px 0 rgb(0 0 0 / 0.5);
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --color-bg: #121212; --color-fg: #fafafa; --color-fg-muted: #a1a1a1; --cds-text-secondary: #a1a1a1;
  --color-panel: #1a1a1a; --pb-inner: #242424; --color-border-line: #2e2e2e;
  --cds-surface-popover: #262626; --cds-border: #404040;
  --cds-chart-grid: #2a2a2a; --cds-chart-axis: #404040; --cds-chart-reference: #737373; --cds-chart-muted: #404040;
  --cds-chart-categorical-1: #3392ff; --cds-chart-categorical-2: #fb64b6; --cds-chart-categorical-3: #00d5be; --cds-chart-categorical-4: #c27aff;
  --cds-chart-categorical-5: #fdc700; --cds-chart-categorical-6: #00bcff; --cds-chart-categorical-7: #9ae600; --cds-chart-categorical-8: #7c86ff;
  --pb-shadow-xs: 0 1px 2px 0 rgb(0 0 0 / 0.3); --cds-shadow-popover: 0 4px 16px 0 rgb(0 0 0 / 0.5);
  color-scheme: dark;
}
body {
  background: var(--color-bg); color: var(--color-fg); font-family: var(--font-anthropic-sans);
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  padding-block: 28px 48px; -webkit-text-size-adjust: 100%;
}
.pb-wrap { max-width: 1200px; margin-inline: auto; }
.pb {
  --pb-accent: var(--cds-chart-categorical-1);
  --pb-hover: color-mix(in srgb, var(--color-fg) 4%, transparent);
  --pb-line-hover: color-mix(in srgb, var(--color-fg) 22%, var(--pb-inner));
  display: grid; gap: var(--cds-gap-lg); font-family: var(--font-anthropic-sans); font-size: var(--cds-font-size-body); color: var(--color-fg);
}
.pb-source { color: var(--color-fg-muted); font-size: var(--cds-font-size-caption); border-top: 1px solid var(--color-border-line); padding-top: 12px; }
"""

SHIM = """
(function () {
  const RAW = JSON.parse(document.getElementById('pb-data').textContent);
  const DEFAULTS = JSON.parse(document.getElementById('pb-params').textContent);
  let params = { ...DEFAULTS };
  const sets = {};
  for (const [id, rows] of Object.entries(RAW)) {
    sets[id] = { status: 'ok', data: rows, columns: Object.keys(rows[0] || {}), refreshing: false, message: '', meta: [] };
  }
  const calcs = [], draws = new Map(), watchers = [];
  const runCalcs = () => {
    for (const c of calcs) {
      try { sets[c.id] = { status: 'ok', data: c.fn(...c.inputs.map((i) => sets[i].data)), columns: [], refreshing: false, message: '', meta: [] }; }
      catch (e) { console.error('calc ' + c.id, e); sets[c.id] = { status: 'error', data: [], columns: [], refreshing: false, message: String(e), meta: [] }; }
    }
  };
  const shown = (el) => !el.closest('[hidden]');
  const render = () => {
    for (const fn of watchers) { try { fn(); } catch (e) { console.error(e); } }
    for (const [name, fn] of draws) {
      document.querySelectorAll('[data-draw="' + name + '"]').forEach((el) => {
        if (!shown(el)) return;
        try { fn(el); } catch (e) { console.error('draw ' + name, e); }
      });
    }
  };
  let queued = false;
  const schedule = () => { if (queued) return; queued = true; requestAnimationFrame(() => { queued = false; render(); }); };
  window.dash = {
    data: (id) => sets[id] || { status: 'missing', data: [], columns: [], refreshing: false, message: '', meta: [] },
    draw: (name, fn) => {
      if (fn === undefined) { schedule(); return; }
      if (typeof fn !== 'function') {
        const made = new WeakMap();
        const spec = fn;
        fn = (el) => { if (!made.has(el)) { el.replaceChildren(); made.set(el, spec.mount ? spec.mount(el) : undefined); } if (spec.update) spec.update(el, made.get(el)); };
      }
      draws.set(name, fn); schedule();
    },
    onData: (fn) => { watchers.push(fn); try { fn(); } catch (e) { console.error(e); } schedule(); },
    calc: (id, spec) => { calcs.push({ id, inputs: spec.inputs, fn: spec.fn }); runCalcs(); schedule(); },
    loader: () => {},
    params: () => ({ ...params }),
    setParams: (p) => { for (const [k, v] of Object.entries(p || {})) { if (v === null || v === undefined) delete params[k]; else params[k] = v; } schedule(); },
    resetParams: () => { params = { ...DEFAULTS }; schedule(); },
    colors: [1, 2, 3, 4, 5, 6, 7, 8].map((i) => 'var(--cds-chart-categorical-' + i + ')'),
    setLink: (name) => { try { history.replaceState(null, '', '#' + name); } catch (e) { /* the frame may refuse it */ } },
    refresh: () => {},
  };
  const root = document.querySelector('.pb');
  let lastW = 0;
  if (root && window.ResizeObserver) new ResizeObserver(() => { const w = root.clientWidth; if (Math.abs(w - lastW) > 1) { lastW = w; schedule(); } }).observe(root);
  const pages = new MutationObserver(schedule);
  document.querySelectorAll('.pb-page').forEach((s) => pages.observe(s, { attributes: true, attributeFilter: ['hidden'] }));
})();
"""


def build(out: Path) -> None:
    page = (HERE / "index.html").read_text()
    css = page[page.index("<style>") + len("<style>"):page.index("</style>")]
    css = css[css.index(".pb-head {"):]                      # component rules; tokens come from HEAD
    markup = page[page.index("</style>") + len("</style>"):page.index("<script>")].strip()
    script = page[page.index("<script>") + len("<script>"):page.rindex("</script>")]
    data = {k: json.loads((DATA / f"{k}.json").read_text()) for k in DATASETS}
    data = {k: (v if isinstance(v, list) else v.get("rows", v)) for k, v in data.items()}
    as_json = lambda o: json.dumps(o, separators=(",", ":")).replace("</", "<\\/")
    foot = ('<p class="pb-source">Data: College Sports Commission, NIL Go Transparency Report and School Revenue-Share '
            'Compensation Report; CollegeFootballData.com for rosters, production and SP+. '
            'Source: github.com/RohanRepala0/College_Football_NIL_Models.</p>')
    markup = markup[:markup.rindex("</div>")] + foot + "\n</div>"
    html = (HEAD + css + "</style>\n\n<div class=\"pb-wrap\">\n" + markup + "\n</div>\n"
            f'<script type="application/json" id="pb-data">{as_json(data)}</script>\n'
            f'<script type="application/json" id="pb-params">{as_json(DEFAULT_PARAMS)}</script>\n'
            f"<script>{SHIM}</script>\n<script>{script}</script>\n")
    out.write_text(html)
    print(f"wrote {out} ({len(html.encode()) / 1e3:.0f} KB)")


if __name__ == "__main__":
    build(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "standalone.html")
