"""Structural and provenance checks for the final corrected course paper."""

from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "output" / "pdf" / "graph_card_control_course_paper.pdf"
PACKAGE = ROOT / "final_results" / "course_paper"
TABLES = PACKAGE / "tables"
FIGURES = PACKAGE / "figures"


def main() -> None:
    with (TABLES / "15_all_1116_game_results.csv").open(newline="", encoding="utf-8") as handle:
        games = list(csv.DictReader(handle))
    assert len(games) == 1116, f"Expected 1116 game rows, found {len(games)}"
    keys = {(row["mode"], row["pair"], row["game"]) for row in games}
    assert len(keys) == 1116, "Game-level table contains duplicate mode/pair/game keys"
    assert all(row["mode"].startswith("corrected_") for row in games)

    with (TABLES / "07_coverage_manifest.csv").open(newline="", encoding="utf-8") as handle:
        coverage = list(csv.DictReader(handle))
    assert len(coverage) == 15
    assert all(row["coverage_ok"].lower() == "true" for row in coverage)

    pngs = sorted(FIGURES.glob("*.png"))
    vector_pdfs = sorted(FIGURES.glob("*.pdf"))
    assert len(pngs) == len(vector_pdfs) == 7
    for path in pngs:
        with Image.open(path) as image:
            dpi = image.info.get("dpi", (0, 0))
            assert min(dpi) >= 295, f"{path.name} is not a 300-dpi export: {dpi}"
            assert min(image.size) >= 600, f"{path.name} is unexpectedly small: {image.size}"

    reader = PdfReader(str(PAPER))
    assert 6 <= len(reader.pages) <= 10, f"Unexpected page count: {len(reader.pages)}"
    page_text = [page.extract_text() or "" for page in reader.pages]
    assert all(len(text.strip()) > 150 for text in page_text), "Blank or nearly blank PDF page"
    text = "\n".join(page_text)
    required = [
        "Omri Avital", "208693341", "Itai Reder", "318850781",
        "Introduction and Literature Review", "Methodology", "Experimental Results",
        "Experimental Conclusions", "1,116", "public-information",
    ]
    for phrase in required:
        assert phrase in text, f"Missing required PDF text: {phrase}"
    forbidden = ["Anonymous course submission", "seed-conditioned implementations"]
    for phrase in forbidden:
        assert phrase not in text, f"Stale legacy phrase remains: {phrase}"

    print(
        f"Validated {len(games)} sorted game rows, {len(coverage)} modes, "
        f"7 raster/vector figure pairs, and {len(reader.pages)} nonblank PDF pages."
    )


if __name__ == "__main__":
    main()
