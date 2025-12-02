"""Extract text content from PDF resume."""

from pypdf import PdfReader


def extract_resume_text(pdf_path: str) -> str:
    """
    Extract all text from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted text as a single string

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        Exception: If PDF cannot be read
    """
    reader = PdfReader(pdf_path)
    text_parts = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)

    return "\n".join(text_parts)


if __name__ == "__main__":
    # Quick test
    import sys

    if len(sys.argv) > 1:
        text = extract_resume_text(sys.argv[1])
        print(text[:1000])
        print(f"\n... Total length: {len(text)} characters")
