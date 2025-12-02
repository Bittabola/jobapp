"""Render cover letter as HTML using Jinja2 template."""

from datetime import date
from functools import lru_cache

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from app.config import PERSONAL_INFO, TEMPLATES_DIR, JobInfo


@lru_cache(maxsize=1)
def _get_jinja_env() -> Environment:
    """Get cached Jinja2 environment with template loader."""
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )


def render_cover_letter_html(cover_letter_text: str, job_info: JobInfo) -> str:
    """
    Render cover letter text into HTML using Jinja2 template.

    Args:
        cover_letter_text: Generated cover letter body (paragraphs)
        job_info: JobInfo dataclass with job details

    Returns:
        Complete HTML string ready for PDF conversion
    """
    env = _get_jinja_env()
    template = env.get_template("cover_letter.html")

    # Convert paragraphs to HTML (mark as safe to prevent escaping)
    paragraphs = cover_letter_text.strip().split("\n\n")
    content_html = Markup(
        "\n".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())
    )

    # Format date
    today = date.today().strftime("%B %d, %Y")

    # Render template with context
    html = template.render(
        name=PERSONAL_INFO["name"],
        title=PERSONAL_INFO["title"],
        location=PERSONAL_INFO["location"],
        email=PERSONAL_INFO["email"],
        phone=PERSONAL_INFO["phone"],
        linkedin=PERSONAL_INFO["linkedin"],
        date=today,
        content=content_html,
    )

    return html


if __name__ == "__main__":
    # Quick test
    test_text = """This is the first paragraph of my cover letter.

This is the second paragraph with more details.

This is the closing paragraph."""

    test_job = JobInfo(
        title="Test Position",
        company="Test Company",
        description="Test description",
    )
    result = render_cover_letter_html(test_text, test_job)
    print(result[:1500])
