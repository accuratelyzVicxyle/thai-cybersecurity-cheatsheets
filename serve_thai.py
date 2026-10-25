#!/usr/bin/env python3
"""Serve the reviewed Thai Markdown cheatsheets on port 9596."""

from __future__ import annotations

import html
import re
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import markdown


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "thai"
ZIP = ROOT / "Thai-CyberSEA-Cheatsheets.zip"
MERMAID = ROOT / "static" / "mermaid.min.js"
PORT = 9596

STYLE = """
:root { color-scheme: dark; --bg:#0b1020; --panel:#121a2d; --ink:#e9eefb;
  --muted:#9faecc; --accent:#67e8f9; --line:#2a3754; --code:#080d19; }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--ink); font:16px/1.68 system-ui,sans-serif; }
header { position:sticky; top:0; z-index:2; padding:.75rem 1rem; background:#0b1020ee;
  border-bottom:1px solid var(--line); backdrop-filter:blur(10px); }
header a { color:var(--accent); margin-right:1.2rem; text-decoration:none; }
main { max-width:1100px; margin:auto; padding:2rem clamp(1rem,4vw,3rem) 5rem; }
h1,h2,h3 { line-height:1.25; scroll-margin-top:5rem; } h1 { color:#fff; }
a { color:var(--accent); } blockquote { border-left:4px solid var(--accent); margin-left:0;
  padding:.2rem 1rem; color:var(--muted); background:var(--panel); }
pre { overflow:auto; padding:1rem; border:1px solid var(--line); border-radius:9px; background:var(--code); }
code { font-family:ui-monospace,SFMono-Regular,Consolas,monospace; background:var(--code); padding:.12em .3em; }
pre code { padding:0; } table { display:block; overflow:auto; border-collapse:collapse; }
th,td { border:1px solid var(--line); padding:.45rem .7rem; vertical-align:top; }
th { background:var(--panel); } hr { border:0; border-top:1px solid var(--line); }
img { display:block; max-width:100%; height:auto; margin:1rem auto; border-radius:8px; }
.missing-image { padding:.8rem 1rem; color:var(--muted); border:1px dashed var(--line);
  border-radius:8px; background:var(--panel); }
.diagram-shell { margin:1rem 0 2rem; border:1px solid var(--line); border-radius:10px;
  overflow:hidden; background:white; }
.diagram-toolbar { position:sticky; top:0; left:0; z-index:1; display:flex; gap:.5rem;
  align-items:center; padding:.55rem .7rem; color:#172033; background:#eef3fb;
  border-bottom:1px solid #cbd5e1; }
.diagram-toolbar span { margin-right:auto; font-size:.9rem; }
.diagram-toolbar button { min-width:2.4rem; padding:.3rem .65rem; border:1px solid #94a3b8;
  border-radius:6px; background:white; color:#172033; cursor:pointer; font-weight:700; }
.diagram-viewport { overflow:auto; max-height:78vh; }
.mermaid { width:max-content; min-width:100%; padding:1.2rem; background:white; }
.mermaid svg { max-width:none !important; height:auto !important; display:block; }
"""


def document_names() -> list[str]:
    return sorted(p.name for p in DOCS.glob("*.md") if p.name != "README.md")


def render_page(name: str) -> bytes:
    path = DOCS / name
    source = path.read_text(encoding="utf-8")
    source = re.sub(
        r"!\[\]\(\s*\)",
        '<p class="missing-image">ไม่มีภาพนี้อยู่ในไฟล์ที่ export จาก Google Docs</p>',
        source,
    )
    body = markdown.markdown(
        source,
        extensions=["fenced_code", "tables", "toc", "sane_lists"],
    )
    known_docs = {"README.md", *document_names()}

    def rewrite_doc_link(match: re.Match[str]) -> str:
        target = html.unescape(urllib.parse.unquote(match.group(1)))
        if target in known_docs:
            return f'href="/view/{urllib.parse.quote(target)}"'
        return match.group(0)

    body = re.sub(r'href="([^"?#]+\.md)"', rewrite_doc_link, body)
    title = "Thai CyberSEA Cheatsheets" if name == "README.md" else name
    page = f"""<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><link rel="icon" href="data:,"><style>{STYLE}</style>
<script src="/assets/mermaid.min.js"></script></head><body>
<header><a href="/">หน้าหลัก</a><a href="/download">ดาวน์โหลด ZIP</a>
<a href="/raw/{urllib.parse.quote(name)}">Markdown ต้นฉบับ</a></header>
<main>{body}</main>
<script>
document.addEventListener('DOMContentLoaded', async () => {{
  const codeNodes = [...document.querySelectorAll('code.language-mermaid')];
  if (!codeNodes.length || !window.mermaid) return;
  const diagrams = codeNodes.map((node, index) => {{
    const shell = document.createElement('section');
    shell.className = 'diagram-shell';
    const toolbar = document.createElement('div');
    toolbar.className = 'diagram-toolbar';
    toolbar.innerHTML = '<span>ลากแถบเลื่อนเพื่อดูแผนผัง • ใช้ปุ่มเพื่อซูม</span><button data-action="out">−</button><button data-action="fit">พอดี</button><button data-action="in">+</button>';
    const viewport = document.createElement('div');
    viewport.className = 'diagram-viewport';
    const diagram = document.createElement('div');
    diagram.className = 'mermaid';
    diagram.id = `mermaid-${{index}}`;
    diagram.textContent = node.textContent;
    viewport.appendChild(diagram);
    shell.append(toolbar, viewport);
    node.parentElement.replaceWith(shell);
    return {{diagram, shell, toolbar, viewport}};
  }});
  try {{
    mermaid.initialize({{startOnLoad:false, theme:'neutral', securityLevel:'loose'}});
    await mermaid.run({{nodes: diagrams.map(item => item.diagram)}});
    diagrams.forEach(item => {{
      const svg = item.diagram.querySelector('svg');
      if (!svg) return;
      const readableWidth = Math.max(2200, item.viewport.clientWidth * 2.4);
      let width = readableWidth;
      const applyWidth = () => {{ svg.style.width = `${{Math.round(width)}}px`; }};
      applyWidth();
      item.toolbar.addEventListener('click', event => {{
        const action = event.target.dataset.action;
        if (!action) return;
        if (action === 'in') width = Math.min(width * 1.25, 7000);
        if (action === 'out') width = Math.max(width / 1.25, 700);
        if (action === 'fit') width = Math.max(item.viewport.clientWidth - 32, 700);
        applyWidth();
      }});
    }});
  }} catch (error) {{
    console.error('Mermaid render failed:', error);
  }}
}});
</script></body></html>"""
    return page.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def send_bytes(self, data: bytes, content_type: str, filename: str | None = None) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/":
            self.send_bytes(render_page("README.md"), "text/html; charset=utf-8")
            return
        if parsed.path == "/download" and ZIP.is_file():
            self.send_bytes(ZIP.read_bytes(), "application/zip", ZIP.name)
            return
        if parsed.path == "/assets/mermaid.min.js" and MERMAID.is_file():
            self.send_bytes(MERMAID.read_bytes(), "text/javascript; charset=utf-8")
            return
        if parsed.path.startswith("/view/"):
            name = urllib.parse.unquote(parsed.path.removeprefix("/view/"))
            if name in document_names():
                self.send_bytes(render_page(name), "text/html; charset=utf-8")
                return
        if parsed.path.startswith("/raw/"):
            name = urllib.parse.unquote(parsed.path.removeprefix("/raw/"))
            if name == "README.md" or name in document_names():
                data = (DOCS / name).read_bytes()
                self.send_bytes(data, "text/markdown; charset=utf-8")
                return
        self.send_error(404)

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} - {fmt % args}", flush=True)


if __name__ == "__main__":
    print(f"Serving Thai cheatsheets at http://0.0.0.0:{PORT}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
