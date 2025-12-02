"""Merge multiple PDFs into one and add page numbers."""

import io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER


def merge_pdfs(pdf_paths: list[str], output_path: str) -> str:
    """
    Merge multiple PDF files into a single PDF with page numbers.

    Args:
        pdf_paths: List of paths to PDF files (in order)
        output_path: Path for the merged output PDF

    Returns:
        Path to merged PDF file
    """
    writer = PdfWriter()

    # First, collect all pages
    all_pages = []
    for pdf_path in pdf_paths:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            all_pages.append(page)

    total_pages = len(all_pages)

    # Add page numbers to each page
    for i, page in enumerate(all_pages, start=1):
        # Create a PDF with just the page number
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=LETTER)

        # Position: bottom center, matching resume style
        page_width = LETTER[0]
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0.3, 0.3, 0.3)  # Gray color
        c.drawCentredString(page_width / 2, 30, f"{i}/{total_pages}")
        c.save()

        # Merge the page number overlay onto the page
        packet.seek(0)
        overlay = PdfReader(packet)
        page.merge_page(overlay.pages[0])
        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path


if __name__ == "__main__":
    # Quick test
    import sys

    if len(sys.argv) >= 3:
        inputs = sys.argv[1:-1]
        output = sys.argv[-1]
        result = merge_pdfs(inputs, output)
        print(f"Merged PDF saved to: {result}")
    else:
        print("Usage: python -m app.pdf_merger input1.pdf input2.pdf output.pdf")
