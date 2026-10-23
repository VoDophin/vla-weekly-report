"""Build the weekly-report HTML from its Markdown source."""
from pathlib import Path
import html
import re


ROOT = Path(__file__).absolute().parent


def inline(text: str) -> str:
    spans = []

    def stash_code(match: re.Match) -> str:
        token = f"INLINECODE{len(spans)}END"
        spans.append((token, f"<code>{html.escape(match.group(1))}</code>"))
        return token

    text = re.sub(r"`([^`\n]+)`", stash_code, text)
    text = html.escape(text)
    text = re.sub(
        r"\[([^]]+)\]\((https://[^)]+)\)",
        r'<a href="\2">\1</a>',
        text,
    )
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    for token, markup in spans:
        text = text.replace(token, markup)
    return text


def render(source: str) -> str:
    lines = source.splitlines()
    blocks = []
    paragraph = []
    i = 0

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append("<p>" + inline(" ".join(paragraph)) + "</p>")
            paragraph.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            i += 1
            continue

        if stripped == "---":
            flush_paragraph()
            blocks.append("<hr>")
            i += 1
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            blocks.append("<pre>" + html.escape("\n".join(code)) + "</pre>")
            i += 1
            continue

        if stripped.startswith("|"):
            flush_paragraph()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [cell.strip() for cell in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"[-: ]+", cell) for cell in cells):
                    rows.append(cells)
                i += 1
            table_rows = []
            for row_index, row in enumerate(rows):
                tag = "th" if row_index == 0 else "td"
                table_rows.append(
                    "<tr>" + "".join(f"<{tag}>{inline(cell)}</{tag}>" for cell in row) + "</tr>"
                )
            blocks.append('<div class="tablewrap"><table>' + "".join(table_rows) + "</table></div>")
            continue

        if stripped.startswith("#"):
            flush_paragraph()
            level = len(stripped) - len(stripped.lstrip("#"))
            blocks.append(f"<h{level}>" + inline(stripped[level:].strip()) + f"</h{level}>")
            i += 1
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            blocks.append("<blockquote>" + inline(stripped[1:].strip()) + "</blockquote>")
            i += 1
            continue

        if re.match(r"^[-*] ", stripped):
            flush_paragraph()
            items = []
            while i < len(lines) and re.match(r"^\s*[-*] ", lines[i]):
                items.append(re.sub(r"^\s*[-*] ", "", lines[i]).strip())
                i += 1
            blocks.append("<ul>" + "".join(f"<li>{inline(item)}</li>" for item in items) + "</ul>")
            continue

        if re.match(r"^\d+\. ", stripped):
            flush_paragraph()
            items = []
            while i < len(lines) and re.match(r"^\s*\d+\. ", lines[i]):
                items.append(re.sub(r"^\s*\d+\. ", "", lines[i]).strip())
                i += 1
            blocks.append("<ol>" + "".join(f"<li>{inline(item)}</li>" for item in items) + "</ol>")
            continue

        paragraph.append(stripped)
        i += 1

    flush_paragraph()
    return "\n".join(blocks)


STYLE = """
:root{color-scheme:light;--ink:#203038;--muted:#5f7076;--accent:#245f63;--accent2:#3f8580;--paper:#fbfaf6;--wash:#e8f0ed;--line:#ccd9d7;--code:#1f2b2e}
*{box-sizing:border-box}body{margin:0;background:#eef1ed;color:var(--ink);font:17px/1.78 system-ui,-apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:980px;margin:32px auto;padding:54px 64px 72px;background:var(--paper);box-shadow:0 14px 46px #314a4822;border-radius:12px}
h1{margin:0 0 .5em;padding-bottom:.45em;color:#153f45;font-size:2.25em;line-height:1.22;border-bottom:4px solid #a8c8c5}
h2{margin:2.2em 0 .9em;padding:.48em .72em;color:#174e54;background:var(--wash);border-left:6px solid var(--accent2);border-radius:0 9px 9px 0;font-size:1.5em;line-height:1.4}
h3{margin:1.8em 0 .65em;padding-bottom:.28em;color:#2c6570;border-bottom:2px solid #d5e2df;font-size:1.23em;line-height:1.5}
h4{margin:1.4em 0 .55em;color:#3d6268;font-size:1.08em}p{margin:.72em 0}strong{color:#173f45}a{color:#0f6670;text-underline-offset:3px}
ul,ol{margin:.65em 0 1em;padding-left:1.55em}li{margin:.34em 0}hr{border:0;border-top:1px solid var(--line);margin:2.6em 0}
code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:.9em;background:#e7ece9;border-radius:4px;padding:.08em .32em}
pre{overflow-x:auto;margin:1em 0;padding:16px 18px;border-radius:9px;background:var(--code);color:#edf5f2;font:15px/1.6 ui-monospace,SFMono-Regular,Consolas,monospace}
blockquote{margin:1.2em 0;padding:.8em 1.1em;background:#edf3f0;border-left:5px solid #6aa19c;color:#28454a;border-radius:0 7px 7px 0}
.tablewrap{overflow-x:auto;margin:1.05em 0 1.35em;border:1px solid var(--line);border-radius:9px}table{border-collapse:collapse;width:100%;min-width:650px;background:#fff}th{background:#dfecea;color:#204f55}th,td{padding:11px 13px;border-bottom:1px solid #d7e1df;text-align:left;vertical-align:top}tr:last-child td{border-bottom:0}
@media(max-width:700px){body{font-size:16px}main{margin:0;padding:28px 18px 48px;border-radius:0}h1{font-size:1.8em}h2{font-size:1.3em;padding:.42em .58em}h3{font-size:1.12em}}
@media print{body{background:#fff}main{max-width:none;margin:0;padding:0;box-shadow:none}a{color:inherit;text-decoration:none}h2,h3{break-after:avoid}.tablewrap,pre,blockquote{break-inside:avoid}}
"""


if __name__ == "__main__":
    source = (ROOT / "本周汇报.md").read_text(encoding="utf-8")
    body = render(source)
    page = (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>本周汇报：从多峰动作生成到 π 系列 VLA</title>'
        f"<style>{STYLE}</style></head><body><main>{body}</main></body></html>"
    )
    assert page.count("<table>") == page.count("</table>")
    assert page.count("<pre>") == page.count("</pre>")
    assert "<!--" not in page
    (ROOT / "本周汇报.html").write_text(page, encoding="utf-8")
    # GitHub Pages serves index.html at the repository root.
    (ROOT / "index.html").write_text(page, encoding="utf-8")
    print("Built weekly report HTML and GitHub Pages index; structure checks passed.")

