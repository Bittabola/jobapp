"""Generate a strategic plan for the cover letter."""

import json
from dataclasses import dataclass
from typing import List

from google import genai
from app.config import GEMINI_MODEL, JobInfo, logger, APP_DIR

RESUME_PATH = APP_DIR / "data/resume.md"


@dataclass
class JobStrategy:
    """Strategic plan for the cover letter."""

    top_requirements: List[str]
    matching_evidence: List[str]
    narrative_hook: str
    tone_suggestion: str


def generate_strategy(job_info: JobInfo) -> JobStrategy:
    """
    Analyze job vs resume to create a writing strategy.

    Args:
        job_info: The target job details.

    Returns:
        JobStrategy object with requirements, evidence, and hook.
    """
    # 1. Load Resume
    try:
        resume_content = RESUME_PATH.read_text()
    except FileNotFoundError:
        logger.error(f"Resume not found at {RESUME_PATH}")
        # Fallback empty if file missing (shouldn't happen with our setup)
        resume_content = "Resume content not available."

    # 2. Build Prompt
    prompt = f"""
    You are a Career Strategist. Analyze the following Resume and Job Description to create a winning cover letter strategy.

    === RESUME ===
    {resume_content}

    === JOB DESCRIPTION ===
    Title: {job_info.title}
    Company: {job_info.company}

    {job_info.description}

    === CRITICAL PRINCIPLE: IMPACT OVER DUTIES ===

    The biggest mistake in professional writing: describing what the job WAS instead of what the candidate DID.

    - DUTY (bad): "Managed inventory" — this is what any person in that role does
    - IMPACT (good): "Reduced inventory errors by reorganizing stock system" — this is what CHANGED

    For every piece of evidence, ask: "What changed, improved, or got fixed because of this person?"

    AVOID these weak framings in your evidence:
    - "responsible for..." (empty, says nothing about results)
    - "worked on..." (vague, implies no ownership)
    - "helped with..." / "assisted in..." (diminishes contribution)
    - "handled..." (generic, no indication of skill or outcome)

    PREFER evidence that shows:
    - Specific metrics (reduced by X%, increased by Y, saved $Z)
    - Problems solved (fixed, eliminated, resolved)
    - Things built or created (built, launched, introduced, designed)
    - Leadership moments (led, trained, drove, spearheaded)
    - Trust earned (was the go-to person for X, chosen to handle Y)

    === TASK ===
    1. Identify the top 3 most critical requirements from the job description (hard skills, soft skills, or responsibilities — ignoring generic fluff like "team player").

    2. For EACH requirement, find the single strongest IMPACT statement from the resume:
       - Must show what CHANGED or IMPROVED, not just what they did
       - Include specific metrics, outcomes, or results when available
       - If the resume uses weak language ("helped", "assisted"), mentally upgrade it to what they actually accomplished
       - If no direct match exists, find the closest transferable achievement

    3. Draft a "Narrative Hook": A 1-sentence opening concept that:
       - Connects a specific, impressive result from the candidate to what the company needs
       - Avoids generic openings like "I am writing to express my interest..."
       - Feels like the start of a conversation, not a formal letter

    4. Suggest a Tone based on company culture inferred from the JD:
       - "Direct & Results-Focused" — for companies that emphasize metrics/outcomes
       - "Warm & Collaborative" — for culture-focused companies
       - "Senior & Strategic" — for leadership roles
       - "Enthusiastic & Curious" — for startups or innovative companies

    Return the result strictly as valid JSON:
    {{
        "top_requirements": ["req1", "req2", "req3"],
        "matching_evidence": ["IMPACT statement for req1", "IMPACT statement for req2", "IMPACT statement for req3"],
        "narrative_hook": "string",
        "tone_suggestion": "string"
    }}
    """

    # 3. Call Gemini
    logger.info(f"Generating application strategy for {job_info.company}...")
    client = genai.Client()

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        data = json.loads(response.text)

        return JobStrategy(
            top_requirements=data.get("top_requirements", []),
            matching_evidence=data.get("matching_evidence", []),
            narrative_hook=data.get("narrative_hook", ""),
            tone_suggestion=data.get("tone_suggestion", "Professional"),
        )
    except Exception as e:
        logger.error(f"Strategy generation failed: {e}")
        # Fallback
        return JobStrategy(
            top_requirements=["Relevant Experience"],
            matching_evidence=["See resume for details"],
            narrative_hook="I am writing to express my interest...",
            tone_suggestion="Professional",
        )
