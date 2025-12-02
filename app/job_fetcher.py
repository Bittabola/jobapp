"""Fetch and parse job descriptions from URLs."""

import re
import requests
from bs4 import BeautifulSoup

from app.config import JobInfo, HTTP_TIMEOUT_SECONDS, logger


def fetch_job_description(url: str) -> JobInfo:
    """
    Fetch job posting from URL and extract key information.

    Args:
        url: Job posting URL (LinkedIn or other)

    Returns:
        JobInfo dataclass with title, company, description, url

    Raises:
        requests.RequestException: If URL cannot be fetched
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    logger.info(f"Fetching job description from: {url}")
    response = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract job info (LinkedIn-specific selectors, with fallbacks)
    title = _extract_title(soup)
    company = _extract_company(soup)
    description = _extract_description(soup)

    logger.info(f"Extracted job: {title} at {company}")
    return JobInfo(
        title=title,
        company=company,
        description=description,
        url=url,
    )


def _extract_title(soup: BeautifulSoup) -> str:
    """Extract job title from page."""
    # Try LinkedIn-specific selectors
    selectors = [
        "h1.top-card-layout__title",
        "h1.topcard__title",
        "h1",
    ]
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            return element.get_text(strip=True)
    return "Unknown Position"


def _extract_company(soup: BeautifulSoup) -> str:
    """Extract company name from page."""
    selectors = [
        "a.topcard__org-name-link",
        "span.topcard__flavor",
        ".top-card-layout__card .topcard__org-name-link",
    ]
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            return element.get_text(strip=True)
    return "Unknown Company"


def _extract_description(soup: BeautifulSoup) -> str:
    """Extract job description from page."""
    selectors = [
        ".description__text",
        ".show-more-less-html__markup",
        "div.description",
        "article",
    ]
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            # Get text and clean up whitespace
            text = element.get_text(separator="\n", strip=True)
            # Remove excessive blank lines
            text = re.sub(r"\n{3,}", "\n\n", text)
            return text

    # Fallback: get all paragraph text
    paragraphs = soup.find_all("p")
    return "\n".join(p.get_text(strip=True) for p in paragraphs[:20])


if __name__ == "__main__":
    # Quick test
    import sys
    import json

    if len(sys.argv) > 1:
        result = fetch_job_description(sys.argv[1])
        print(json.dumps(result, indent=2)[:2000])
