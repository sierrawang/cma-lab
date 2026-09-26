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
    # Code blocks: a label and a Copy button.
    def code(match):
        lang = match.group(1) or ""
        return (f'<div class="code"><div class="codebar"><span>{LABELS.get(lang, lang)}</span>'
                f'<button class="copy">Copy</button></div><pre><code>{match.group(2)}</code></pre></div>')
    body = re.sub(r'<pre><code(?: class="language-(\w+)")?>(.*?)</code></pre>', code, body, flags=re.S)
    # "✅ You know it worked when…" paragraphs (and the list after them) become green callouts.
    body = re.sub(r"<p>✅ (.*?)</p>\s*(<ul>.*?</ul>)?", lambda m: f'<div class="check"><p>{m.group(1)}</p>{m.group(2) or ""}</div>',
                  body, flags=re.S)
    body = body.replace("<blockquote>", '<div class="note">').replace("</blockquote>", "</div>")
    body = body.replace("<table>", '<div class="tablewrap"><table>').replace("</table>", "</table></div>")
    return body


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{ --ink: #1f2937; --muted: #6b7280; --line: #e5e7eb; --accent: #c2410c; --bg: #fbfaf8; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--ink); font: 17px/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
  main {{ max-width: 780px; margin: 0 auto; padding: 48px 24px 120px; }}
  h1 {{ font-size: 34px; line-height: 1.2; margin: 0 0 20px; letter-spacing: -0.01em; }}
  h2 {{ font-size: 25px; margin: 56px 0 8px; padding-top: 24px; border-top: 1px solid var(--line); }}
  h3 {{ font-size: 19px; margin: 36px 0 6px; }}
  p, li {{ margin: 8px 0; }}
  a {{ color: var(--accent); }}
  hr {{ display: none; }}
  code {{ font: 0.86em ui-monospace, SFMono-Regular, Menlo, monospace; background: #f1efeb; padding: 1px 5px; border-radius: 5px; }}
  .code {{ margin: 14px 0; border: 1px solid #2d3340; border-radius: 10px; overflow: hidden; background: #161b22; }}
  .codebar {{ min-height: 30px; display: flex; justify-content: space-between; align-items: center; padding: 6px 10px 6px 14px; background: #20262f;
             color: #9ca3af; font-size: 12px; letter-spacing: .04em; text-transform: uppercase; }}
  .copy {{ font: 12px -apple-system, sans-serif; color: #e5e7eb; background: #313845; border: 0; border-radius: 6px; padding: 4px 10px; cursor: pointer; }}
  .copy:hover {{ background: #3d4553; }}
  .code pre {{ margin: 0; padding: 14px 16px; white-space: pre-wrap; overflow-wrap: anywhere; }}
  .code code {{ background: none; padding: 0; color: #e6edf3; font-size: 14px; line-height: 1.55; }}
  .tablewrap {{ overflow-x: auto; margin: 16px 0; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 15px; background: #fff; border: 1px solid var(--line); border-radius: 10px; }}
  th, td {{ text-align: left; padding: 9px 12px; border-bottom: 1px solid var(--line); vertical-align: top; }}
  th {{ font-size: 13px; color: var(--muted); font-weight: 600; background: #f7f6f3; }}
  tr:last-child td {{ border-bottom: 0; }}
  .check {{ margin: 18px 0; padding: 10px 16px; background: #ecfdf3; border: 1px solid #b7ebc9; border-radius: 10px; }}
  .check p:first-child::before {{ content: "✓"; display: inline-block; width: 22px; height: 22px; margin-right: 8px; border-radius: 50%;
                                  background: #16a34a; color: #fff; text-align: center; line-height: 22px; font-size: 13px; font-weight: 700; }}
  .check ul {{ margin: 4px 0 4px 30px; padding-left: 16px; }}
  .note {{ margin: 18px 0; padding: 10px 16px; background: #fff7ed; border: 1px solid #fed7aa; border-radius: 10px; }}
  details {{ margin: 12px 0; background: #fff; border: 1px solid var(--line); border-radius: 10px; }}
  summary {{ cursor: pointer; padding: 10px 14px; font-weight: 600; color: var(--accent); }}
  details .inner {{ padding: 0 14px 6px; }}
  .tabs {{ margin: 14px 0; background: #fff; border: 1px solid var(--line); border-radius: 10px; }}
  .tabbar {{ display: flex; gap: 4px; padding: 8px 8px 0; border-bottom: 1px solid var(--line); }}
  .tab {{ font: 600 14px -apple-system, sans-serif; color: var(--muted); background: none; border: 0; padding: 8px 14px;
          border-bottom: 2px solid transparent; cursor: pointer; }}
  .tab.on {{ color: var(--accent); border-bottom-color: var(--accent); }}
  .pane {{ display: none; padding: 4px 16px 8px; }}
  .pane.on {{ display: block; }}
</style></head>
<body><main>
{body}
</main>
<script>
  // Copy buttons
  document.querySelectorAll(".copy").forEach(button => button.addEventListener("click", async () => {{
    const text = button.closest(".code").querySelector("code").innerText.replace(/\\n$/, "");
    try {{ await navigator.clipboard.writeText(text); }}
    catch {{ const t = document.createElement("textarea"); t.value = text; document.body.appendChild(t); t.select(); document.execCommand("copy"); t.remove(); }}
    button.textContent = "Copied!"; setTimeout(() => button.textContent = "Copy", 1500);
  }}));
  // Computer tabs: picking one switches every set of tabs, and the page remembers it
  function pick(os) {{
    document.querySelectorAll(".tab").forEach(t => t.classList.toggle("on", t.dataset.os === os));
    document.querySelectorAll(".pane").forEach(p => p.classList.toggle("on", p.dataset.os === os));
    try {{ localStorage.setItem("lab-os", os); }} catch {{}}
  }}
  document.querySelectorAll(".tab").forEach(t => t.addEventListener("click", () => pick(t.dataset.os)));
  let saved = null; try {{ saved = localStorage.getItem("lab-os"); }} catch {{}}
  pick(saved || (navigator.platform.toLowerCase().includes("mac") ? "Mac" : "Linux or Windows"));
</script>
</body></html>
"""


if __name__ == "__main__":
    md = SOURCE.read_text()
    title = re.search(r"^# (.+)$", md, re.M).group(1)
    OUT.write_text(PAGE.format(title=html.escape(title), body=decorate(convert(md))))
    print("wrote", OUT.name)
