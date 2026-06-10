"""Load source documents into clean text + metadata.

We support Markdown (the self-authored corpus) and PDF (datasheets you add locally).
The job here is deliberately small and transparent: read a file, get its text, and
remember *where* each piece of text came from. That provenance (file name, and for PDFs
the page number) is what later lets every answer carry a citation.

We do NOT chunk here — that is `chunk.py`'s job. A `Document` is one whole file's worth of
text, optionally split into "blocks" that each know their source location.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Block:
    """A contiguous span of text with a known location in its source document."""

    text: str
    source: str  # file name, e.g. "soh_methods.md"
    locator: str  # human-readable position: a Markdown heading path or "p.3" for a PDF page


@dataclass
class Document:
    """One source file, parsed into ordered blocks plus its raw full text."""

    source: str
    blocks: list[Block] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n\n".join(b.text for b in self.blocks)


# --- Markdown ---------------------------------------------------------------------------

_FRONTMATTER = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


def _strip_frontmatter(text: str) -> str:
    """Remove a leading YAML front-matter block if present (it's metadata, not content)."""
    return _FRONTMATTER.sub("", text, count=1)


def load_markdown(path: Path) -> Document:
    """Parse a Markdown file into blocks, one per heading section.

    Each block's locator is the heading path (e.g. "State of Health > Capacity-based SOH"),
    which makes citations readable: a reader can find exactly the section an answer used.
    Text before the first heading is kept under a "(intro)" locator so nothing is lost.
    """
    raw = _strip_frontmatter(path.read_text(encoding="utf-8"))
    blocks: list[Block] = []

    # Track the current heading at each level to build a breadcrumb path.
    heading_stack: list[str] = []
    current_locator = "(intro)"
    buffer: list[str] = []

    def flush() -> None:
        body = "\n".join(buffer).strip()
        if body:
            blocks.append(Block(text=body, source=path.name, locator=current_locator))
        buffer.clear()

    for line in raw.splitlines():
        m = _HEADING.match(line)
        if m:
            flush()  # close the previous section before starting a new one
            level = len(m.group(1))
            title = m.group(2).strip()
            heading_stack = heading_stack[: level - 1]
            heading_stack.append(title)
            current_locator = " > ".join(heading_stack)
        else:
            buffer.append(line)
    flush()

    return Document(source=path.name, blocks=blocks)


# --- PDF --------------------------------------------------------------------------------


def load_pdf(path: Path) -> Document:
    """Parse a PDF into one block per page, locator "p.<n>".

    We try `pdfplumber` first because it handles datasheet tables more gracefully, and fall
    back to `pypdf`. PDFs are imported lazily so the Markdown path has no heavy dependency.
    """
    blocks: list[Block] = []
    try:
        import pdfplumber

        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = (page.extract_text() or "").strip()
                if text:
                    blocks.append(Block(text=text, source=path.name, locator=f"p.{i}"))
    except Exception:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        for i, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                blocks.append(Block(text=text, source=path.name, locator=f"p.{i}"))

    return Document(source=path.name, blocks=blocks)


# --- Directory --------------------------------------------------------------------------

_LOADERS = {".md": load_markdown, ".markdown": load_markdown, ".pdf": load_pdf}


def load_document(path: Path) -> Document:
    loader = _LOADERS.get(path.suffix.lower())
    if loader is None:
        raise ValueError(f"Unsupported file type: {path.suffix} ({path})")
    return loader(path)


def load_corpus(corpus_dir: Path) -> list[Document]:
    """Load every supported document in a directory, sorted for deterministic ordering."""
    docs: list[Document] = []
    for path in sorted(corpus_dir.iterdir()):
        if path.suffix.lower() in _LOADERS and path.is_file():
            docs.append(load_document(path))
    return docs
