"""Generate cover letter using Gemini AI, humanize with OpenAI."""

from google import genai
from openai import OpenAI

from app.config import (
    GEMINI_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    PROMPTS_DIR,
    JobInfo,
    logger,
)


def generate_cover_letter(
    resume_text: str, job_info: JobInfo, dynamic_instructions: str = ""
) -> str:
    """
    Generate a tailored cover letter using Gemini AI.

    Args:
        resume_text: Extracted text from resume PDF
        job_info: JobInfo dataclass with title, company, description
        dynamic_instructions: Job-specific instructions from user

    Returns:
        Generated cover letter body text (paragraphs only)
    """
    # Load static prompt
    static_prompt = _load_static_prompt()

    # Build full prompt
    full_prompt = f"""{static_prompt}

=== CANDIDATE'S RESUME ===
{resume_text}

=== TARGET JOB ===
Company: {job_info.company}
Position: {job_info.title}

Job Description:
{job_info.description}

=== SPECIFIC INSTRUCTIONS FOR THIS APPLICATION ===
{dynamic_instructions if dynamic_instructions else "None provided - use your best judgment based on the job requirements."}

Now write the cover letter body paragraphs:"""

    # Call Gemini API (uses GEMINI_API_KEY env var automatically)
    logger.info(f"Generating cover letter for {job_info.title} at {job_info.company}")
    client = genai.Client()
    response = client.models.generate_content(model=GEMINI_MODEL, contents=full_prompt)

    return response.text.strip()


def humanize_cover_letter(cover_letter_text: str) -> str:
    """
    Rewrite a cover letter to sound more naturally human using OpenAI.

    Uses a different model (GPT-5.1) than the generator (Gemini) to create
    a different linguistic fingerprint, which helps avoid AI detection.

    Args:
        cover_letter_text: The AI-generated cover letter text

    Returns:
        Humanized cover letter text with more natural variation
    """
    humanizer_prompt = _load_prompt("humanizer_prompt.txt")

    full_prompt = f"""{humanizer_prompt}

=== COVER LETTER TO REWRITE ===
{cover_letter_text}

Now rewrite this cover letter with more natural, human-like variation:"""

    logger.info(f"Humanizing cover letter with {OPENAI_MODEL}")
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "user", "content": full_prompt},
        ],
    )

    return response.choices[0].message.content.strip()


def _load_prompt(filename: str) -> str:
    """Load a prompt file from the prompts directory."""
    prompt_file = PROMPTS_DIR / filename
    try:
        with open(prompt_file, "r") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {prompt_file}")
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")


def _load_static_prompt() -> str:
    """Load the static cover letter prompt from file."""
    return _load_prompt("general_prompt.txt")


if __name__ == "__main__":
    # Quick test (requires GEMINI_API_KEY env var)
    test_job = JobInfo(
        title="Marketing Manager",
        company="Test Corp",
        description="Looking for experienced marketing professional...",
    )
    result = generate_cover_letter(
        resume_text="Experienced marketer with 10 years...",
        job_info=test_job,
        dynamic_instructions="Focus on digital marketing experience",
    )
    print(result)
