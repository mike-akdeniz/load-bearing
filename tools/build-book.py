#!/usr/bin/env python3
"""Build the book as a PDF and an EPUB.

    python3 tools/build-book.py            # both, into build/
    python3 tools/build-book.py pdf        # or just one
    python3 tools/build-book.py epub

Needs pandoc, and tectonic for the PDF (`brew install pandoc tectonic`).

The chapters are read in the order 00_toc.md gives, under its six parts.
The source is written for GitHub, so the build changes three things on the way
through, and nothing in the source changes:

- A link to another chapter's file becomes a link to that chapter in the book,
  keyed on the four-character identifier in its filename, which never changes.
- The navigation line at the foot of each chapter (← Ch. 04 · Contents ·
  Ch. 06 →) is dropped; the book has its own contents and page order.
- The introduction is README.md without the lines that only make sense on
  GitHub, and a relative link to a repository file becomes a GitHub URL.
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
REPO_URL = "https://github.com/mike-akdeniz/load-bearing"
LINKEDIN_URL = "https://www.linkedin.com/in/mike-ilke-akdeniz-888ab321/"
ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI"}

CHAPTER_FILE = re.compile(r"^(\d\d)_[a-z0-9-]+_([a-z0-9]{4})\.md$")
CHAPTER_LINK = re.compile(r"\]\((\d\d_[a-z0-9-]+_([a-z0-9]{4}))\.md\)")
NAV_LINE = re.compile(r"^\[← .*\]\(.*\)\s*$|^\[Contents\]\(00_toc\.md\)")
BOX_DRAWING = re.compile(r"[\u2190-\u21ff\u2500-\u25ff]")

# The LaTeX side. Long code lines wrap with a visible ↪ (the setup the book's
# CLAUDE.md specifies); Charter has no arrow, so → comes from the math font;
# `text` blocks that draw a diagram are left unwrapped,
# because a wrapped diagram is destroyed rather than merely marked.
LATEX_HEADER = r"""
\usepackage{fvextra}
\fvset{
  breaklines=true,
  breakanywhere=false,
  breakindent=2em,
  breaksymbolleft={\small\ensuremath{\hookrightarrow}},
  fontsize=\small
}
\RecustomVerbatimEnvironment{verbatim}{Verbatim}{breaklines=false,fontsize=\small}
% The title page is drawn by front_matter(); pandoc's own is switched off.
\renewcommand{\maketitle}{}
\usepackage{xurl}
\usepackage{tikz}
\usepackage{newunicodechar}
\newunicodechar{→}{\ensuremath{\rightarrow}}
\setlength{\emergencystretch}{3em}
\setcounter{tocdepth}{0}
\PassOptionsToPackage{hypertexnames=false}{hyperref}
"""

# Lua: tag each `text` block as diagram or not, so the PDF wraps terminal
# output but never a drawing. The EPUB ignores the distinction.
LUA_FILTER = r"""
-- Link text that is itself a URL has no spaces, so LaTeX cannot break it and
-- it runs off the page. Give it break points after / and before . - # _.
function Link(el)
  if not FORMAT:match("latex") then return nil end
  local text = pandoc.utils.stringify(el.content)
  if text:find("%s") or not text:find("/") then return nil end
  local out = {}
  for piece, sep in text:gmatch("([^/%.%-#_]*)([/%.%-#_]?)") do
    if piece ~= "" then table.insert(out, pandoc.Str(piece)) end
    if sep == "/" then
      table.insert(out, pandoc.Str("/"))
      table.insert(out, pandoc.RawInline("latex", "\\allowbreak{}"))
    elseif sep ~= "" then
      table.insert(out, pandoc.RawInline("latex", "\\allowbreak{}"))
      table.insert(out, pandoc.Str(sep))
    end
  end
  el.content = out
  return el
end

-- The same for long inline code that is a path or a dotted name.
function Code(el)
  if not FORMAT:match("latex") then return nil end
  if #el.text < 20 or not el.text:match("^[%w%./_%-]+$") then return nil end
  local tex = el.text:gsub("_", "\\_")
  tex = tex:gsub("([/%.])", "%1\\allowbreak{}")
  return pandoc.RawInline("latex", "\\texttt{" .. tex .. "}")
end

function CodeBlock(el)
  if FORMAT:match("latex") and el.classes:includes("text") then
    if el.text:find("[\226][\134-\135\148-\151]") then
      return pandoc.RawBlock("latex",
        "\\begin{Verbatim}[breaklines=false,fontsize=\\small]\n" .. el.text .. "\n\\end{Verbatim}")
    end
    return pandoc.RawBlock("latex",
      "\\begin{Verbatim}[breaklines=true,breakanywhere=true,fontsize=\\small,breaksymbolleft={\\small\\ensuremath{\\hookrightarrow}}]\n" .. el.text .. "\n\\end{Verbatim}")
  end
end
"""

EPUB_CSS = """
body { font-family: serif; line-height: 1.5; }
code, pre { font-family: monospace; }
pre { white-space: pre-wrap; font-size: 0.8em; background: #f6f6f6; padding: 0.6em; }
pre.text { white-space: pre; overflow-x: auto; }
blockquote { margin-left: 1.5em; font-style: italic; }
h1 { page-break-before: always; }
"""


def version():
    out = subprocess.run(["git", "describe", "--tags", "--always"], cwd=ROOT,
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()


def parts_and_chapters():
    """[(part title, [chapter file, ...]), ...] in 00_toc.md order."""
    parts = []
    for line in (ROOT / "00_toc.md").read_text().splitlines():
        if m := re.match(r"^## Part [IVX]+ — (.+)$", line):
            parts.append((m.group(1), []))
        elif m := re.match(r"^- \d\d\. \[.*\]\((\d\d_[^)]+\.md)\)$", line):
            parts[-1][1].append(m.group(1))
    files = {p.name for p in ROOT.glob("[0-9][0-9]_*.md")} - {"00_toc.md"}
    listed = {f for _, fs in parts for f in fs}
    if files != listed:
        sys.exit(f"00_toc.md and the chapter files disagree: {sorted(files ^ listed)}")
    return parts


def chapter_markdown(path, fmt):
    num, ident = CHAPTER_FILE.match(path.name).groups()
    lines = path.read_text().splitlines()

    # Drop the "*Part I: ...*" line above a part's first chapter title; the
    # book has a part page of its own.
    while lines and (not lines[0].strip() or re.match(r"^\*Part [IVX]+: .*\*$", lines[0])):
        lines.pop(0)

    # Drop the navigation footer and the rule above it.
    while lines and (not lines[-1].strip() or NAV_LINE.match(lines[-1])):
        lines.pop()
    if lines and lines[-1].strip() == "---":
        lines.pop()

    text = "\n".join(lines) + "\n"
    # Chapters become level 2 under their part, so every heading moves down one.
    text = re.sub(r"^(#+) ", r"#\1 ", text, flags=re.M)
    # LaTeX numbers parts and chapters itself; an EPUB has to be told.
    prefix = f"{int(num)}. " if fmt == "epub" else ""
    text = re.sub(r"^## (.+)$", rf"## {prefix}\1 {{#ch-{ident}}}", text, count=1, flags=re.M)
    return relink(text)


def relink(text):
    text = CHAPTER_LINK.sub(lambda m: f"](#ch-{m.group(2)})", text)
    # Anything else relative points at a file in the repository.
    return re.sub(r"\]\((?!https?:|#|mailto:)([^)]+)\)",
                  lambda m: f"]({REPO_URL}/blob/main/{m.group(1)})", text)


def introduction(fmt):
    """README.md as the book's introduction, minus the GitHub-only lines."""
    out, skipping = [], False
    for line in (ROOT / "README.md").read_text().splitlines():
        if line.startswith("## "):
            # "What's in it" describes the contents, which follow in the book.
            skipping = line.startswith("## What's in it")
        if skipping:
            continue
        if line.startswith(("# ", "*Which Software")):
            continue  # the title page carries these
        if line.startswith(("**→", "→ [", "By [")):
            continue  # links into the repository's own pages
        if line.startswith("**Status:"):
            continue  # the copyright page carries the version
        out.append(line)
    body = "\n".join(out).strip() + "\n"
    # In the PDF the introduction is a chapter, under the part division. An
    # EPUB given a level-2 heading before any level-1 one invents an empty
    # level-1 section to hold it, so there it is a top-level section. Its own
    # subsections stay at level 3 either way: the EPUB starts a new page at 2.
    level = "##" if fmt == "pdf" else "#"
    body = re.sub(r"^## ", "### ", body, flags=re.M)
    return f"{level} Introduction {{.unnumbered}}\n\n" + relink(body)


def metadata(ver):
    return f"""---
title: "Load-Bearing"
subtitle: "Which Software Principles Hold, and Where They Stop"
author: "Mike Akdeniz"
date: "{ver}"
lang: en
rights: "© 2026 Mike Akdeniz. Licensed under CC BY-NC 4.0."
---
"""


def front_matter(ver):
    # The cover (tools/make-cover.py) on a page filled with its own paper colour,
    # since the letter page is wider than the cover. Then the title page:
    # title, subtitle and author at 1.5 times the class's own sizes
    # (\LARGE and \large at 11pt are 20.7pt and 12pt).
    return rf"""
```{{=latex}}
\begin{{titlepage}}
\pagecolor[HTML]{{F3EFE6}}
\begin{{tikzpicture}}[remember picture,overlay]
\node at (current page.center) {{\includegraphics[height=\paperheight]{{{ROOT / "docs" / "cover.png"}}}}};
\end{{tikzpicture}}
\end{{titlepage}}
\nopagecolor
\begin{{titlepage}}
\centering
\vspace*{{0.25\textheight}}
{{\fontsize{{31}}{{38}}\selectfont Load-Bearing\par}}
\vspace{{1.2em}}
{{\fontsize{{18}}{{23}}\selectfont Which Software Principles Hold, and Where They Stop\par}}
\vspace{{2.5em}}
{{\fontsize{{18}}{{23}}\selectfont Mike Akdeniz\par}}
\vspace{{1em}}
{{\large {ver}\par}}
\end{{titlepage}}
\frontmatter
\tableofcontents
\mainmatter
```
"""


def colophon_pdf(ver):
    return rf"""
```{{=latex}}
\backmatter
\clearpage
\thispagestyle{{empty}}
\noindent\small
Load-Bearing: Which Software Principles Hold, and Where They Stop\\
\copyright{{}} 2026 Mike Akdeniz\\[1em]
Licensed under Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0):\\
\url{{https://creativecommons.org/licenses/by-nc/4.0/}}\\[1em]
Version {ver}. Source, history and every editorial decision:\\
\url{{{REPO_URL}}}\\[1em]
The author on LinkedIn:\\
\url{{{LINKEDIN_URL}}}
\normalsize
```
"""


def colophon_epub(ver):
    return f"""# About this book {{.unnumbered}}

*Load-Bearing: Which Software Principles Hold, and Where They Stop*, © 2026 Mike Akdeniz.

Licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).

Version {ver}. Source, history and every editorial decision: [{REPO_URL.removeprefix("https://")}]({REPO_URL}).

The author on LinkedIn: [{LINKEDIN_URL.removeprefix("https://www.")}]({LINKEDIN_URL}).
"""


def assemble(fmt, ver):
    out = [metadata(ver)]
    if fmt == "pdf":
        out.append(front_matter(ver))
    out.append(introduction(fmt))
    for n, (part, files) in enumerate(parts_and_chapters(), 1):
        label = f"Part {ROMAN[n]}: " if fmt == "epub" else ""
        out.append(f"# {label}{part}\n")
        for f in files:
            out.append(chapter_markdown(ROOT / f, fmt))
    out.append(colophon_pdf(ver) if fmt == "pdf" else colophon_epub(ver))
    return "\n\n".join(out)


def build(fmt):
    ver = version()
    BUILD.mkdir(exist_ok=True)
    src = BUILD / f"book-{fmt}.md"
    src.write_text(assemble(fmt, ver))
    lua = BUILD / "filter.lua"
    lua.write_text(LUA_FILTER)

    common = ["pandoc", str(src), "--from", "markdown-implicit_figures",
              "--top-level-division=part", "--lua-filter", str(lua)]
    if fmt == "pdf":
        cmd = common + [
            "--pdf-engine=tectonic", "-o", str(BUILD / "load-bearing.pdf"),
            "-V", "documentclass=book", "-V", "classoption=oneside",
            "-V", "papersize=letter", "-V", "geometry=margin=1in",
            "-V", "fontsize=11pt", "-V", "mainfont=Charter",
            "-V", "monofont=Menlo", "-V", "monofontoptions=Scale=0.85",
            "-V", "colorlinks=true", "-V", "linkcolor=black",
            "-V", "urlcolor=blue",
            "--number-sections", "-V", "secnumdepth=0",
            "-H", str(write(BUILD / "header.tex", LATEX_HEADER)),
        ]
    else:
        cmd = common + [
            "-o", str(BUILD / "load-bearing.epub"), "--toc", "--toc-depth=2",
            "--split-level=2",
            "--css", str(write(BUILD / "epub.css", EPUB_CSS)),
        ]
        cover = ROOT / "docs" / "cover.png"
        if cover.exists():
            cmd += ["--epub-cover-image", str(cover)]
    subprocess.run(cmd, cwd=ROOT, check=True)
    print(f"built {BUILD / ('load-bearing.' + fmt)} ({ver})")


def write(path, text):
    path.write_text(text)
    return path


if __name__ == "__main__":
    for tool in ("pandoc", "tectonic"):
        if not shutil.which(tool):
            sys.exit(f"{tool} not found: brew install pandoc tectonic")
    for fmt in sys.argv[1:] or ["pdf", "epub"]:
        build(fmt)
