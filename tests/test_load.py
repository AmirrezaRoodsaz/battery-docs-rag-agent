"""Tests for document loading — front-matter stripping and heading-path locators."""

from pathlib import Path

from src.ingest.load import load_markdown


def _write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_frontmatter_is_stripped(tmp_path):
    md = "---\ntitle: T\nauthor: A\n---\n# Heading\n\nBody text here.\n"
    doc = load_markdown(_write(tmp_path, "a.md", md))
    assert "title: T" not in doc.text
    assert "Body text here." in doc.text


def test_heading_path_locators(tmp_path):
    md = "# Top\n\nintro under top\n\n## Sub\n\nsub body\n\n### Deep\n\ndeep body\n"
    doc = load_markdown(_write(tmp_path, "b.md", md))
    locators = {b.locator for b in doc.blocks}
    assert "Top" in locators
    assert "Top > Sub" in locators
    assert "Top > Sub > Deep" in locators


def test_text_before_first_heading_is_kept(tmp_path):
    md = "preamble before any heading\n\n# Real Heading\n\nbody\n"
    doc = load_markdown(_write(tmp_path, "c.md", md))
    intro = [b for b in doc.blocks if b.locator == "(intro)"]
    assert intro and "preamble" in intro[0].text


def test_source_is_filename(tmp_path):
    doc = load_markdown(_write(tmp_path, "soh_methods.md", "# H\n\nx\n"))
    assert all(b.source == "soh_methods.md" for b in doc.blocks)
