"""Turn README.md into docs/index.html (the GitHub Pages site): a self-contained page with copy buttons and computer tabs.

Run: python3 make_lab_html.py
Edit the Markdown, not the HTML. The Markdown stays readable on its own (GitHub, VS Code).
"""
import html
import re
from pathlib import Path

import markdown

HERE = Path(__file__).parent
SOURCE, OUT = HERE / "README.md", HERE / "docs" / "index.html"
EXTENSIONS = ["fenced_code", "tables", "toc", "sane_lists"]
LABELS = {"bash": "Terminal", "python": "Python", "yaml": "YAML", "markdown": "Markdown", "": ""}


def render(md):
    return markdown.markdown(md, extensions=EXTENSIONS)


def convert(md):
    md = re.sub(r"(?m)^([^\n\s-][^\n]*)\n(- )", r"\1\n\n\2", md)
    blocks = []  # rendered HTML for <details> sections, swapped in after the main render

    def keep(rendered):
        blocks.append(rendered)
        return f"\n\n@@BLOCK{len(blocks) - 1}@@\n\n"

    # Runs of "Mac" / "Linux or Windows" sections become one set of tabs.
    details = r"<details>\s*<summary>(.*?)</summary>(.*?)</details>"
    def tabs(match):
        items = re.findall(details, match.group(0), re.S)
        buttons = "".join(f'<button class="tab" data-os="{html.escape(t.strip())}">{html.escape(t.strip())}</button>'
                          for t, _ in items)
        panes = "".join(f'<div class="pane" data-os="{html.escape(t.strip())}">{render(body)}</div>' for t, body in items)
        return keep(f'<div class="tabs"><div class="tabbar">{buttons}</div>{panes}</div>')
    os_detail = r"<details>\s*<summary>(?:Mac|Linux or Windows)</summary>.*?</details>"
    md = re.sub(rf"(?:{os_detail}\s*)+", tabs, md, flags=re.S)
    # Other <details> (hints, answers) stay collapsible.
    md = re.sub(details, lambda m: keep(f'<details><summary>{html.escape(m.group(1))}</summary>'
                                        f'<div class="inner">{render(m.group(2))}</div></details>'), md, flags=re.S)

    body = render(md)
    body = re.sub(r"<p>@@BLOCK(\d+)@@</p>", lambda m: blocks[int(m.group(1))], body)
    return body


def decorate(body):
    # Code blocks: a small label and a Copy button.
    def code(match):
        lang = match.group(1) or ""
        label = f'<span class="lang">{LABELS.get(lang, lang)}</span>' if LABELS.get(lang, lang) else ""
        return (f'<div class="code">{label}<button class="copy" aria-label="Copy">Copy</button>'
                f'<pre><code>{match.group(2)}</code></pre></div>')
    body = re.sub(r'<pre><code(?: class="language-(\w+)")?>(.*?)</code></pre>', code, body, flags=re.S)
    # "✅ You know it worked when…" paragraphs (and the list after them) become callouts.
    body = re.sub(r"<p>✅ (.*?)</p>\s*(<ul>.*?</ul>)?", lambda m: f'<div class="check"><p>{m.group(1)}</p>{m.group(2) or ""}</div>',
                  body, flags=re.S)
    body = body.replace("<blockquote>", '<div class="note">').replace("</blockquote>", "</div>")
    body = body.replace("<table>", '<div class="tablewrap"><table>').replace("</table>", "</table></div>")
    body = re.sub(r"<hr\s*/?>", "", body)
    return body


def sections(body):
    """Split the page at each ## heading. Returns (intro, [(id, title, subsections, html)])."""
    parts = re.split(r'(?=<h2 id=")', body)
    out = []
    for part in parts[1:]:
        sid, title = re.match(r'<h2 id="([^"]+)">(.*?)</h2>', part).groups()
        subs = re.findall(r'<h3 id="([^"]+)">(.*?)</h3>', part)
        out.append((sid, title, subs, part))
    return parts[0], out


def build(md):
    body = decorate(convert(md))
    intro, secs = sections(body)
    intro = re.sub(r"<h1[^>]*>.*?</h1>", "", intro, flags=re.S)
    intro = re.sub(r'<div class="tablewrap">.*?</div>', "", intro, count=1, flags=re.S)  # the sidebar replaces the contents table
    nav, main = [], []
    for sid, title, subs, part in secs:
        trackable = not title.lower().startswith(("if something", "extensions"))
        box = (f'<input type="checkbox" class="done" data-id="{sid}" aria-label="Mark {html.escape(re.sub("<.*?>", "", title))} done">'
               if trackable else '<span class="nobox"></span>')
        sub = "".join(f'<a class="sub" href="#{i}">{t}</a>' for i, t in subs)
        nav.append(f'<div class="navsec" data-id="{sid}"><div class="navrow">{box}<a class="top" href="#{sid}">{title}</a></div>'
                   f'<div class="subs">{sub}</div></div>')
        if trackable:
            part += (f'<div class="finish"><button class="mark" data-id="{sid}">Mark “{re.sub("<.*?>", "", title)}” as done</button></div>')
        main.append(f'<section id="sec-{sid}">{part}</section>')
    return "".join(nav), intro + "".join(main)


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{ --ink: #141413; --body: #3d3d3a; --muted: #73726c; --line: #e8e6dc; --soft: #f0eee6; --bg: #faf9f5;
           --accent: #c6613f; --green: #4d7c4a; --serif: "Tiempos Headline", "Iowan Old Style", Georgia, serif;
           --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
           --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace; }}
  * {{ box-sizing: border-box; }}
  html {{ scroll-behavior: smooth; scroll-padding-top: 24px; }}
  body {{ margin: 0; background: var(--bg); color: var(--body); font: 16px/1.7 var(--sans); -webkit-font-smoothing: antialiased; }}
  .layout {{ display: flex; min-height: 100vh; }}
  nav {{ position: sticky; top: 0; height: 100vh; width: 290px; flex: none; overflow-y: auto;
         padding: 32px 20px 40px 28px; border-right: 1px solid var(--line); }}
  nav .brand {{ font: 500 19px/1.3 var(--serif); color: var(--ink); margin: 0 0 6px; }}
  nav .progress {{ font-size: 13px; color: var(--muted); margin-bottom: 22px; }}
  nav .bar {{ height: 3px; background: var(--soft); border-radius: 3px; margin-top: 8px; overflow: hidden; }}
  nav .bar span {{ display: block; height: 100%; width: 0; background: var(--accent); transition: width .3s; }}
  .navsec {{ margin-bottom: 4px; }}
  .navrow {{ display: flex; align-items: center; gap: 10px; }}
  .navrow a.top {{ flex: 1; padding: 6px 10px; border-radius: 8px; color: var(--ink); font-size: 15px; font-weight: 500; text-decoration: none; }}
  .navrow a.top:hover {{ background: var(--soft); }}
  .navsec.active a.top {{ background: #ece9df; }}
  .navsec.complete a.top {{ color: var(--muted); }}
  .nobox {{ width: 17px; flex: none; }}
  input.done {{ appearance: none; width: 17px; height: 17px; flex: none; margin: 0; border: 1.5px solid #c3c0b6; border-radius: 50%;
                cursor: pointer; display: grid; place-content: center; background: #fff; }}
  input.done:checked {{ background: var(--green); border-color: var(--green); }}
  input.done:checked::after {{ content: ""; width: 4px; height: 8px; border: solid #fff; border-width: 0 2px 2px 0; transform: translateY(-1px) rotate(45deg); }}
  .subs {{ display: none; margin: 2px 0 8px 27px; border-left: 1px solid var(--line); }}
  .navsec.active .subs {{ display: block; }}
  a.sub {{ display: block; padding: 3px 0 3px 12px; color: var(--muted); font-size: 14px; text-decoration: none; margin-left: -1px; border-left: 1px solid transparent; }}
  a.sub:hover {{ color: var(--ink); }}
  a.sub.active {{ color: var(--ink); border-left-color: var(--ink); }}
  main {{ flex: 1; min-width: 0; }}
  .content {{ max-width: 760px; margin: 0 auto; padding: 56px 40px 160px; }}
  h1 {{ font: 500 40px/1.15 var(--serif); color: var(--ink); margin: 0 0 20px; letter-spacing: -0.01em; }}
  h2 {{ font: 500 30px/1.25 var(--serif); color: var(--ink); margin: 72px 0 12px; }}
  h3 {{ font: 600 18px/1.4 var(--sans); color: var(--ink); margin: 40px 0 6px; }}
  p, li {{ margin: 10px 0; }}
  strong {{ color: var(--ink); font-weight: 600; }}
  a {{ color: var(--ink); text-decoration: underline; text-decoration-color: #b8b5aa; text-underline-offset: 3px; }}
  a:hover {{ text-decoration-color: var(--ink); }}
  :not(pre) > code {{ font: 0.875em var(--mono); color: var(--ink); background: var(--soft); padding: 2px 5px; border-radius: 5px; }}
  .code {{ position: relative; margin: 14px 0 18px; background: #fff; border: 1px solid var(--line); border-radius: 12px; }}
  .code pre {{ margin: 0; padding: 16px 120px 16px 18px; white-space: pre-wrap; overflow-wrap: anywhere; }}
  .code code {{ font: 13.5px/1.5 var(--mono); color: var(--ink); }}
  .code .lang {{ position: absolute; top: 8px; right: 62px; font-size: 11px; color: #a3a198; letter-spacing: .03em; }}
  .copy {{ position: absolute; top: 6px; right: 8px; font: 500 12px var(--sans); color: var(--muted); background: #fff;
           border: 1px solid var(--line); border-radius: 6px; padding: 2px 8px; cursor: pointer; opacity: .75; }}
  .code:hover .copy {{ opacity: 1; }}
  .copy:hover {{ color: var(--ink); border-color: #cfccc1; }}
  .tablewrap {{ overflow-x: auto; margin: 18px 0; border: 1px solid var(--line); border-radius: 12px; background: #fff; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 15px; }}
  th, td {{ text-align: left; padding: 11px 16px; border-bottom: 1px solid var(--line); vertical-align: top; }}
  th {{ font-weight: 600; color: var(--ink); }}
  tr:last-child td {{ border-bottom: 0; }}
  .check {{ margin: 20px 0; padding: 4px 18px 4px 20px; border-left: 3px solid var(--green); background: #f3f5ef; border-radius: 0 10px 10px 0; }}
  .check ul {{ margin: 4px 0 8px; padding-left: 20px; }}
  .note {{ margin: 20px 0; padding: 4px 18px 4px 20px; border-left: 3px solid var(--accent); background: #f7efe9; border-radius: 0 10px 10px 0; }}
  details {{ margin: 12px 0; border: 1px solid var(--line); border-radius: 12px; background: #fff; }}
  summary {{ cursor: pointer; padding: 10px 16px; font-weight: 500; color: var(--ink); }}
  details .inner {{ padding: 0 16px 6px; }}
  .tabs {{ margin: 14px 0 18px; }}
  .tabbar {{ display: flex; gap: 6px; margin-bottom: 4px; }}
  .tab {{ font: 500 15px var(--sans); color: var(--muted); background: none; border: 0; padding: 6px 14px; border-radius: 8px; cursor: pointer; }}
  .tab:hover {{ color: var(--ink); }}
  .tab.on {{ color: var(--ink); background: #ece9df; }}
  .pane {{ display: none; }}
  .pane.on {{ display: block; }}
  .finish {{ margin: 36px 0 0; }}
  .mark {{ font: 500 14px var(--sans); color: var(--ink); background: #fff; border: 1px solid var(--line); border-radius: 999px;
           padding: 8px 16px; cursor: pointer; }}
  .mark:hover {{ border-color: #cfccc1; }}
  .mark.on {{ background: #eef2ea; border-color: #c9d6c3; color: var(--green); }}
  @media (max-width: 900px) {{ nav {{ display: none; }} .content {{ padding: 32px 20px 120px; }} }}
</style></head>
<body><div class="layout">
<nav>
  <div class="brand">{title}</div>
  <div class="progress"><span id="count">0</span> of <span id="total">0</span> done<div class="bar"><span id="fill"></span></div></div>
  {nav}
</nav>
<main><div class="content">
<h1>{title}</h1>
{body}
</div></main>
</div>
<script>
  // Copy buttons
  document.querySelectorAll(".copy").forEach(button => button.addEventListener("click", async () => {{
    const text = button.closest(".code").querySelector("code").innerText.replace(/\\n$/, "");
    try {{ await navigator.clipboard.writeText(text); }}
    catch {{ const t = document.createElement("textarea"); t.value = text; document.body.appendChild(t); t.select(); document.execCommand("copy"); t.remove(); }}
    button.textContent = "Copied"; setTimeout(() => button.textContent = "Copy", 1500);
  }}));

  // Computer tabs: picking one switches every set, and the page remembers it
  const store = {{ get: k => {{ try {{ return localStorage.getItem(k); }} catch {{ return null; }} }},
                  set: (k, v) => {{ try {{ localStorage.setItem(k, v); }} catch {{}} }} }};
  function pick(os) {{
    document.querySelectorAll(".tab").forEach(t => t.classList.toggle("on", t.dataset.os === os));
    document.querySelectorAll(".pane").forEach(p => p.classList.toggle("on", p.dataset.os === os));
    store.set("lab-os", os);
  }}
  document.querySelectorAll(".tab").forEach(t => t.addEventListener("click", () => pick(t.dataset.os)));
  pick(store.get("lab-os") || (navigator.platform.toLowerCase().includes("mac") ? "Mac" : "Linux or Windows"));

  // Milestone checkmarks, saved in this browser
  const done = new Set(JSON.parse(store.get("lab-done") || "[]"));
  function render() {{
    document.querySelectorAll("input.done").forEach(b => {{ b.checked = done.has(b.dataset.id); b.closest(".navsec").classList.toggle("complete", b.checked); }});
    document.querySelectorAll(".mark").forEach(b => {{
      const on = done.has(b.dataset.id); b.classList.toggle("on", on);
      b.textContent = on ? "✓ Done" : b.dataset.label;
    }});
    const total = document.querySelectorAll("input.done").length;
    document.getElementById("count").textContent = [...done].filter(id => document.querySelector(`input.done[data-id="${{id}}"]`)).length;
    document.getElementById("total").textContent = total;
    document.getElementById("fill").style.width = (100 * done.size / Math.max(total, 1)) + "%";
    store.set("lab-done", JSON.stringify([...done]));
  }}
  function toggle(id, on) {{ on ? done.add(id) : done.delete(id); render(); }}
  document.querySelectorAll(".mark").forEach(b => {{ b.dataset.label = b.textContent; b.addEventListener("click", () => toggle(b.dataset.id, !done.has(b.dataset.id))); }});
  document.querySelectorAll("input.done").forEach(b => b.addEventListener("change", () => toggle(b.dataset.id, b.checked)));
  render();

  // Highlight where you are in the sidebar
  const heads = [...document.querySelectorAll(".content h2, .content h3")];
  function spy() {{
    let current = heads[0];
    for (const h of heads) if (h.getBoundingClientRect().top < 120) current = h;
    const sec = current.tagName === "H2" ? current : current.closest("section")?.querySelector("h2");
    document.querySelectorAll(".navsec").forEach(n => n.classList.toggle("active", sec && n.dataset.id === sec.id));
    document.querySelectorAll("a.sub").forEach(a => a.classList.toggle("active", a.getAttribute("href") === "#" + current.id));
  }}
  document.addEventListener("scroll", spy, {{ passive: true }}); spy();
</script>
</body></html>
"""


if __name__ == "__main__":
    md = SOURCE.read_text()
    title = re.search(r"^# (.+)$", md, re.M).group(1)
    nav, body = build(md)
    OUT.write_text(PAGE.format(title=html.escape(title), nav=nav, body=body))
    print("wrote", OUT.relative_to(HERE))
