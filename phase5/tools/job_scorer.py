import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv
import pdfplumber

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_resume(path: str = "phase1/resume.pdf") -> str:
    """Extracts text from resume PDF."""
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def parse_json_safely(raw: str) -> dict:
    """Robust JSON parser — handles LLM preamble text."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not parse JSON from: {raw}")

def score_job(job: dict, resume: str) -> dict:
    """
    Scores a single job dict against the resume.
    Returns the job dict enriched with score, verdict, reason.
    """
    SYSTEM_PROMPT = """
    You are an expert technical recruiter.
    Evaluate how well a candidate's resume matches a job description.
    Respond ONLY with a valid JSON object — no explanation, no markdown.
    {
      "score": <integer 1-10>,
      "verdict": "<STRONG_MATCH | GOOD_MATCH | WEAK_MATCH | NO_MATCH>",
      "matching_skills": ["skill1", "skill2"],
      "missing_skills": ["skill1", "skill2"],
      "reason": "<2-3 sentence explanation>"
    }
    """

    user_message = f"""
    RESUME:
    {resume}

    JOB TITLE: {job['title']}
    COMPANY: {job['company']}
    JOB DESCRIPTION:
    {job['summary']}

    Evaluate the match and respond in JSON only.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        max_tokens=500,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message}
        ]
    )

    result = parse_json_safely(response.choices[0].message.content)

    # Enrich the original job dict with scoring results
    job["score"]          = result.get("score", 0)
    job["verdict"]        = result.get("verdict", "N/A")
    job["matching_skills"]= result.get("matching_skills", [])
    job["missing_skills"] = result.get("missing_skills", [])
    job["reason"]         = result.get("reason", "N/A")

    return job