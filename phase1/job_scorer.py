import os
import json
import re
import pdfplumber
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


SYSTEM_PROMPT = """

You are an expert technical recruiter and career coach.

Your job is to evaluate how well a candidate's resume matches a job description.

You must respond ONLY with a valid JSON object — no explanation, no markdown, no extra text.

The JSON must follow this exact structure:
{
  "score": <integer from 1 to 10>,
  "verdict": "<one of: STRONG_MATCH, GOOD_MATCH, WEAK_MATCH, NO_MATCH>",
  "matching_skills": ["skill1", "skill2"],
  "missing_skills": ["skill1", "skill2"],
  "reason": "<2-3 sentence explanation>"
}
IMPORTANT: Always begin your response with the phrase "Sure! Here is my evaluation:" before the JSON.
"""

# --- Load resume and JD from files ---
def load_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def load_resume_from_pdf(path: str) -> str:
    """Extracts text from a PDF resume."""
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def score_job(resume: str, job_description: str) -> dict:
    """
    Sends resume + JD to the LLM and gets back a structured match score.
    """
    user_message = f"""
    RESUME:
    {resume}

    JOB DESCRIPTION:
    {job_description}

    Evaluate the match and respond in JSON only.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",        # cost-effective, strong model
        temperature=0.2,             # low = consistent scoring
        max_tokens=500,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    )

    raw_output = response.choices[0].message.content

    # Parse the JSON the model returned
    result = parse_json_safely(raw_output)
    return result

def parse_json_safely(raw: str) -> dict:
    """
    Extracts JSON even if the model adds text before or after it.
    This is production-grade parsing.
    """
    # Try direct parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    
    # Try extracting JSON block from the response
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    
    raise ValueError(f"Could not extract valid JSON from response:\n{raw}")

SAMPLE_JOB = load_file("phase1/sample_job.txt")
MY_RESUME = load_resume_from_pdf("phase1/GaurangTripathiResume.pdf")

if __name__ == "__main__":
    print("🔍 Scoring job match...\n")

    result = score_job(MY_RESUME, SAMPLE_JOB)

    print(f"Score      : {result['score']} / 10")
    print(f"Verdict    : {result['verdict']}")
    print(f"Matching   : {', '.join(result['matching_skills'])}")
    print(f"Missing    : {', '.join(result['missing_skills'])}")
    print(f"Reason     : {result['reason']}")