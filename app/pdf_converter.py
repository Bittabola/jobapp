"""Convert HTML to PDF using Playwright."""

import asyncio
from playwright.async_api import async_playwright


async def html_to_pdf_async(html_content: str, output_path: str) -> str:
    """
    Async implementation of HTML to PDF conversion.

    Use this directly in async contexts (e.g., FastAPI handlers).
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Set content and wait for rendering
        await page.set_content(html_content, wait_until="networkidle")

        # Generate PDF (uses CSS @page margins from template)
        await page.pdf(
            path=output_path,
            format="Letter",
            print_background=True,
            prefer_css_page_size=True,
        )

        await browser.close()

    return output_path


def html_to_pdf(html_content: str, output_path: str) -> str:
    """
    Convert HTML string to PDF file (sync version).

    NOTE: Do not call this from an async context (e.g., FastAPI handlers).
    Use html_to_pdf_async() directly instead.

    Args:
        html_content: Complete HTML document as string
        output_path: Path where PDF should be saved

    Returns:
        Path to generated PDF file
    """
    return asyncio.run(html_to_pdf_async(html_content, output_path))


if __name__ == "__main__":
    # Quick test
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @page { size: letter; margin: 0.5in; }
            body { font-family: Arial; }
            .header { background: #1f2937; color: white; padding: 20px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Test PDF</h1>
        </div>
        <p>This is a test paragraph with background colors.</p>
    </body>
    </html>
    """
    result = html_to_pdf(test_html, "/tmp/test_output.pdf")
    print(f"PDF saved to: {result}")
