# JobApp

A self-hosted web app that generates tailored cover letters and merges them with your resume into a single, ready-to-submit PDF.

## Why JobApp?

- **Two-step AI generation** — First, Google Gemini drafts a cover letter tailored to the job posting. Then, OpenAI rewrites it with a different model and prompt to reduce AI detection signals and produce more natural-sounding text.
- **Single merged PDF** — Cover letter + resume combined into one document with consistent page numbering.
- **Privacy-first** — Runs locally on your machine. Your resume and job data never leave your computer (except for API calls to generate text).
- **Customizable prompts** — Edit the AI prompts directly in the UI to match your tone and style.

## Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env with your API keys and personal information
```

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key ([get one here](https://aistudio.google.com/app/apikey)) |
| `OPENAI_API_KEY` | OpenAI API key ([get one here](https://platform.openai.com/api-keys)) |
| `USER_NAME` | Your full name |
| `USER_EMAIL` | Your email address |

See `.env.example` for all configuration options.

## Usage

```bash
python run_web.py
```

Open http://localhost:8000 in your browser.

### Features

- Upload your resume PDF
- Paste a job posting URL or enter job details manually
- Add custom instructions for tailoring
- Edit the AI prompt in Advanced Settings

## Output

The tool produces a single PDF with:
1. Cover letter (first page) - styled to match your resume
2. Your resume (following pages)

## Pipeline

1. **Reading resume** - Extract text from PDF
2. **Fetching job details** - Scrape job posting or use manual input
3. **Generating with AI** - Create cover letter using Gemini
4. **Humanizing text** - Rewrite to reduce AI detection signals
5. **Rendering HTML** - Apply cover letter template
6. **Creating PDF** - Convert HTML to PDF with Playwright
7. **Merging documents** - Combine cover letter + resume
