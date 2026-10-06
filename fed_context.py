import json
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup


STATEMENT_URL = (
    "https://www.federalreserve.gov/"
    "newsevents/pressreleases/"
    "monetary20260916a.htm"
)

TEXT_FILE = Path("fed_context.txt")
METADATA_FILE = Path(
    "fed_context_metadata.json"
)


def download_statement(url):
    """Download the official Federal Reserve page."""
    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": (
                "MacroResearchAssistant/1.0"
            )
        },
    )

    response.raise_for_status()

    return response.text


def extract_text(html):
    """Extract readable text from the HTML page."""
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    for element in soup(
        [
            "script",
            "style",
            "nav",
            "header",
            "footer",
        ]
    ):
        element.decompose()

    text = soup.get_text(
        separator="\n"
    )

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    return "\n".join(lines)


def save_context(text, url):
    """Save the statement and source metadata."""
    retrieved_at = datetime.now(
        timezone.utc
    ).isoformat()

    TEXT_FILE.write_text(
        text,
        encoding="utf-8",
    )

    metadata = {
        "source_type": "official Federal Reserve document",
        "source_url": url,
        "retrieved_at_utc": retrieved_at,
        "document": (
            "Federal Reserve issues FOMC statement"
        ),
    }

    METADATA_FILE.write_text(
        json.dumps(
            metadata,
            indent=4,
        ),
        encoding="utf-8",
    )


def main():
    html = download_statement(
        STATEMENT_URL
    )

    text = extract_text(html)

    if not text:
        raise ValueError(
            "No text was extracted from the "
            "Federal Reserve page."
        )

    save_context(
        text,
        STATEMENT_URL,
    )

    print(f"Saved: {TEXT_FILE}")
    print(f"Saved: {METADATA_FILE}")
    print(
        f"Extracted characters: {len(text)}"
    )


if __name__ == "__main__":
    main()