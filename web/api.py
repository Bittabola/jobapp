"""FastAPI web application with true SSE progress streaming."""

import json
import re
import asyncio
from dataclasses import dataclass
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, StreamingResponse

from app.config import (
    OUTPUT_DIR,
    PROMPTS_DIR,
    FILENAME_SLUG,
    MIN_PROMPT_LENGTH,
    JobInfo,
    logger,
)
from app.pdf_converter import html_to_pdf_async
from app.job_fetcher import fetch_job_description
from app.cover_letter_generator import generate_cover_letter, humanize_cover_letter  # noqa: F401 - humanize_cover_letter paused but kept for easy re-enable
from app.html_renderer import render_cover_letter_html
from app.pdf_merger import merge_pdfs


@dataclass
class PipelineResult:
    """Result of a pipeline execution."""

    success: bool
    pdf_path: Optional[Path] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    error: Optional[str] = None
    step_failed: Optional[str] = None


def sanitize_filename(name: str) -> str:
    """Convert company name to safe filename format."""
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")
    return name


# User-friendly error messages
ERROR_MESSAGES = {
    "resume": "Couldn't read your resume. Please make sure it's a valid PDF file.",
    "job": "Couldn't fetch job details from that URL. Try pasting the job description manually instead.",
    "generate": "AI generation failed. Please try again in a moment.",
    "humanize": "Text humanization failed. Please try again.",
    "render": "Failed to create the cover letter. Please try again.",
    "pdf": "PDF creation failed. Please try again.",
    "merge": "Failed to merge documents. Please try again.",
}

# Step progress messages
STEP_MESSAGES = {
    "resume": "Reading resume...",
    "job": "Fetching job details...",
    "generate": "Generating with AI...",
    "humanize": "Humanizing text...",
    "render": "Rendering HTML...",
    "pdf": "Creating PDF...",
    "merge": "Merging documents...",
}

# Directories
UPLOAD_DIR = Path("uploads")
PROMPT_FILE = PROMPTS_DIR / "general_prompt.txt"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    # Startup: ensure directories exist, clean old uploads
    UPLOAD_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    for f in UPLOAD_DIR.glob("*"):
        f.unlink(missing_ok=True)
    yield
    # Shutdown: nothing to do


app = FastAPI(title="JobApp - Cover Letter Generator", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Templates
templates = Jinja2Templates(directory="web/templates")


async def run_pipeline_async(
    job_url: str | None = None,
    job_description: str | None = None,
    job_title: str | None = None,
    company_name: str | None = None,
    custom_instructions: str = "",
) -> AsyncGenerator[tuple[str, PipelineResult | None], None]:
    """
    Async wrapper for the sync pipeline generator.

    Runs each pipeline step in a thread pool to avoid blocking.
    Uses the same step-based approach but with async PDF conversion.
    """
    OUTPUT_DIR.mkdir(exist_ok=True)

    # NOTE: Resume is now read directly from app/data/resume.md in strategy_generator.py
    # We pass an empty string to generate_cover_letter as legacy placeholder.
    resume_text = ""

    # Step 1: Get job info
    yield ("job", None)
    try:
        if job_url:
            job_info = await asyncio.to_thread(fetch_job_description, job_url)
        else:
            job_info = JobInfo(
                title=job_title or "Unknown",
                company=company_name or "Unknown",
                description=job_description or "",
                url=None,
            )
    except Exception as e:
        logger.error(f"Failed to fetch job: {e}")
        yield (
            "error",
            PipelineResult(
                success=False,
                error=str(e),
                step_failed="job",
            ),
        )
        return

    # Determine output path
    company_slug = sanitize_filename(job_info.company)
    output_path = OUTPUT_DIR / f"{FILENAME_SLUG}_{company_slug}.pdf"

    # Step 2: Generate cover letter with AI
    yield ("generate", None)
    try:
        cover_letter_text = await asyncio.to_thread(
            generate_cover_letter,
            resume_text=resume_text,
            job_info=job_info,
            dynamic_instructions=custom_instructions,
        )
    except Exception as e:
        logger.error(f"AI generation failed: {e}")
        yield (
            "error",
            PipelineResult(
                success=False,
                error=str(e),
                step_failed="generate",
            ),
        )
        return

    # Step 3: Humanize cover letter (reduce AI detection)
    # PAUSED: Skipping humanization to reduce latency and cost.
    # Uncomment the block below to re-enable.
    # yield ("humanize", None)
    # try:
    #     cover_letter_text = await asyncio.to_thread(
    #         humanize_cover_letter,
    #         cover_letter_text,
    #     )
    # except Exception as e:
    #     logger.error(f"Humanization failed: {e}")
    #     yield (
    #         "error",
    #         PipelineResult(
    #             success=False,
    #             error=str(e),
    #             step_failed="humanize",
    #         ),
    #     )
    #     return

    # Step 4: Render HTML
    yield ("render", None)
    try:
        html_content = await asyncio.to_thread(
            render_cover_letter_html, cover_letter_text, job_info
        )
    except Exception as e:
        logger.error(f"HTML rendering failed: {e}")
        yield (
            "error",
            PipelineResult(
                success=False,
                error=str(e),
                step_failed="render",
            ),
        )
        return

    # Step 5: Convert to PDF (native async)
    yield ("pdf", None)
    cover_letter_pdf = OUTPUT_DIR / "cover_letter_temp.pdf"
    try:
        await html_to_pdf_async(html_content, str(cover_letter_pdf))
    except Exception as e:
        logger.error(f"PDF conversion failed: {e}")
        yield (
            "error",
            PipelineResult(
                success=False,
                error=str(e),
                step_failed="pdf",
            ),
        )
        return

    # Step 6: Merge PDFs (if resume.pdf exists)
    yield ("merge", None)

    # Give filesystem a moment to release locks on the temp PDF
    await asyncio.sleep(0.5)

    try:
        # Use absolute path relative to project root
        from app.config import APP_DIR

        # APP_DIR is .../app, so resume is in APP_DIR/data/resume.pdf
        resume_pdf_path = APP_DIR / "data/resume.pdf"

        logger.info(f"Looking for resume at: {resume_pdf_path}")
        logger.info(f"Cover letter at: {cover_letter_pdf}")

        if resume_pdf_path.exists():
            logger.info("Resume found. Merging...")
            await asyncio.to_thread(
                merge_pdfs,
                pdf_paths=[str(cover_letter_pdf), str(resume_pdf_path)],
                output_path=str(output_path),
            )
            logger.info(f"Merge complete. Output: {output_path}")
        else:
            logger.info("Resume not found. Moving cover letter only.")
            # Just rename/move if no resume to merge
            import shutil

            shutil.move(str(cover_letter_pdf), str(output_path))
            logger.info(f"Move complete. Output: {output_path}")

    except Exception as e:
        logger.error(f"PDF merge failed: {e}")
        import traceback

        logger.error(traceback.format_exc())

        # Fallback: Try to save just the cover letter so the user gets something
        try:
            logger.info("Attempting fallback: Saving cover letter only.")
            import shutil

            if cover_letter_pdf.exists():
                shutil.move(str(cover_letter_pdf), str(output_path))
                logger.info(f"Fallback successful. Output: {output_path}")
            else:
                logger.error("Fallback failed: Temp file missing.")
        except Exception as fallback_error:
            logger.error(f"Fallback failed: {fallback_error}")
            # NOW yield the error since even fallback failed
            yield (
                "error",
                PipelineResult(
                    success=False,
                    error=f"Merge and Fallback failed: {e}",
                    step_failed="merge",
                ),
            )
            return

    finally:
        if cover_letter_pdf.exists():
            cover_letter_pdf.unlink()

    # Done!
    logger.info(f"Pipeline complete: {output_path}")
    yield (
        "complete",
        PipelineResult(
            success=True,
            pdf_path=output_path,
            job_title=job_info.title,
            company=job_info.company,
        ),
    )


@app.get("/")
async def home(request: Request):
    """Serve main UI page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/generate")
async def generate(
    job_url: str = Form(None),
    job_description: str = Form(None),
    job_title: str = Form(None),
    company_name: str = Form(None),
    instructions: str = Form(""),
):
    """
    Generate cover letter with true SSE progress streaming.

    Returns a text/event-stream with progress updates as each step completes.
    """
    # Validate inputs
    if not job_url and not (job_description and job_title and company_name):
        return StreamingResponse(
            _error_stream("Provide either a job URL or manual job details"),
            media_type="text/event-stream",
        )

    async def event_stream():
        """Stream SSE events as each pipeline step completes."""
        async for step, result in run_pipeline_async(
            job_url=job_url,
            job_description=job_description,
            job_title=job_title,
            company_name=company_name,
            custom_instructions=instructions,
        ):
            if step == "error" and result:
                # Map step to user-friendly message
                error_msg = ERROR_MESSAGES.get(result.step_failed, "An error occurred")
                yield _sse_event("error", {"error": error_msg})
                return

            if step == "complete" and result:
                yield _sse_event(
                    "complete",
                    {
                        "success": True,
                        "download_url": f"/api/download/{result.pdf_path.name}",
                        "filename": result.pdf_path.name,
                        "job_title": result.job_title,
                        "company": result.company,
                    },
                )
                return

            # Progress step
            if step in STEP_MESSAGES:
                yield _sse_event(
                    "progress",
                    {"step": step, "message": STEP_MESSAGES[step]},
                )

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/download/{filename}")
async def download(filename: str):
    """Download generated PDF."""
    # Secure path validation: resolve and verify within OUTPUT_DIR
    try:
        file_path = (OUTPUT_DIR / filename).resolve()
        if not str(file_path).startswith(str(OUTPUT_DIR.resolve())):
            raise HTTPException(400, "Invalid filename")
    except (ValueError, OSError):
        raise HTTPException(400, "Invalid filename")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(404, "File not found")

    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    import os

    return {"status": "ok", "gemini_configured": bool(os.environ.get("GEMINI_API_KEY"))}


@app.get("/api/prompt")
async def get_prompt():
    """Get current AI prompt text."""
    try:
        prompt_text = PROMPT_FILE.read_text()
        return {"prompt": prompt_text}
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {PROMPT_FILE}")
        raise HTTPException(500, "Prompt file not found")
    except Exception as e:
        logger.error(f"Failed to read prompt file: {e}")
        raise HTTPException(500, "Failed to read prompt file")


@app.put("/api/prompt")
async def save_prompt(request: Request):
    """Save AI prompt to file."""
    try:
        data = await request.json()
        prompt = data.get("prompt", "")
    except Exception as e:
        logger.error(f"Invalid JSON body: {e}")
        raise HTTPException(400, "Invalid JSON body")

    if len(prompt) < MIN_PROMPT_LENGTH:
        raise HTTPException(
            400, f"Prompt too short (minimum {MIN_PROMPT_LENGTH} characters)"
        )

    try:
        PROMPT_FILE.write_text(prompt)
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to save prompt file: {e}")
        raise HTTPException(500, "Failed to save prompt file")


def _sse_event(event: str, data: dict) -> str:
    """Format a Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _error_stream(message: str):
    """Generate an error SSE stream."""
    yield _sse_event("error", {"error": message})
