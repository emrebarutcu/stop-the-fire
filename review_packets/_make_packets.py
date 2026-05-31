"""Split IE492_Final_Report_xelatex.pdf into four equally-weighted reviewer packets.

Work-balancing strategy:
  • Refs (body p. 31) → Packet A. The front-matter reviewer is best placed to
    cross-check that every [n] citation in §1+§2 resolves to the References list.
  • Appendix A (body p. 32, top half) → Packet C. Test config naturally extends
    §5.1's experimental design.
  • Appendix B & C (body pp. 32-33) → Packet D. Code map + API endpoints
    naturally extend §6.1's implementation discussion.
  • Body p. 32 is shared between C and D because Appendix A and the start of
    Appendix B sit on the same physical page. README clarifies who reviews what.

Result (body pages per packet, ignoring shared title+TOC):
  A: 8 (pp. 3-9, 31)
  B: 8 (pp. 10-17)
  C: 7 (pp. 18-23, 32)
  D: 9 (pp. 24-30, 32-33)

PDF page indices are 1-based to match the user-visible numbering.
The PDF page = body page + 3 (after title page + 2 TOC pages).
"""
from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).parent.parent
SRC = ROOT / "IE492_Final_Report_xelatex.pdf"
OUT = ROOT / "review_packets"
OUT.mkdir(parents=True, exist_ok=True)

# Shared front matter: title + TOC pp. 1-2 (PDF pages 1, 2, 3).
FRONTMATTER = [1, 2, 3]


def body_to_pdf(body_page: int) -> int:
    """Convert body page number (3-33) to 1-based PDF page index.

    PDF p. 1 = title page; PDF pp. 2-3 = TOC (body pp. 1-2);
    PDF p. 4 = body p. 3 (Abstract); ...; PDF p. 34 = body p. 33 (Appendix C).
    """
    return body_page + 1


PACKETS = [
    ("A", "Front matter & Problem framing",
     # Body pp. 3-9 (front matter + §1 + §2) and p. 31 (References).
     list(range(3, 10)) + [31]),
    ("B", "Methodology & Strategy development",
     # Body pp. 10-17 (§3 + §4).
     list(range(10, 18))),
    ("C", "Comparison, Recommendation & Test config",
     # Body pp. 18-23 (§5) and p. 32 (Appendix A; also shows start of B).
     list(range(18, 24)) + [32]),
    ("D", "Implementation, Conclusions, Code map & API",
     # Body pp. 24-30 (§6 + §7) and pp. 32-33 (Appendices A continued, B, C).
     list(range(24, 31)) + [32, 33]),
]


def main() -> None:
    reader = PdfReader(str(SRC))
    n = len(reader.pages)
    assert n == 34, f"expected 34 pages, found {n}"

    # Delete old packet files first
    for old in OUT.glob("packet_*.pdf"):
        old.unlink()

    for letter, topic, body_pages in PACKETS:
        writer = PdfWriter()
        pdf_pages = FRONTMATTER + [body_to_pdf(b) for b in body_pages]
        for p in pdf_pages:
            writer.add_page(reader.pages[p - 1])
        slug = (topic.lower()
                .replace(" & ", "_and_")
                .replace(" ", "_")
                .replace(",", ""))
        out_path = OUT / f"packet_{letter}_{slug}.pdf"
        with out_path.open("wb") as f:
            writer.write(f)
        body_str = ", ".join(
            f"{a}-{b}" if a != b else str(a)
            for a, b in _runs(body_pages)
        )
        print(f"packet {letter}: {len(pdf_pages)} PDF pages "
              f"({len(body_pages)} body pp. = {body_str})")


def _runs(pages: list[int]) -> list[tuple[int, int]]:
    """Group consecutive page numbers into (start, end) runs."""
    if not pages:
        return []
    runs = []
    a = b = pages[0]
    for p in pages[1:]:
        if p == b + 1:
            b = p
        else:
            runs.append((a, b))
            a = b = p
    runs.append((a, b))
    return runs


if __name__ == "__main__":
    main()
