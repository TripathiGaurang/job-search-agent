import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from dotenv import load_dotenv

load_dotenv()

GMAIL_ADDRESS      = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


def send_job_digest(to_email: str, jobs: list[dict], query: str, location: str):
    """
    Sends a formatted job digest email via Gmail SMTP.
    Only sends jobs with score >= 7.
    """
    strong_jobs = [j for j in jobs if j.get("score", 0) >= 7]

    if not strong_jobs:
        print("   No strong matches to email.")
        return False

    # Build email content
    subject = f"🎯 {len(strong_jobs)} Job Matches Found — {query} in {location}"
    body    = _build_email_body(strong_jobs, query, location)

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = GMAIL_ADDRESS
        msg["To"]      = to_email

        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())

        print(f"   ✅ Email sent to {to_email}")
        return True

    except Exception as e:
        print(f"   ❌ Email failed: {e}")
        return False


def _build_email_body(jobs: list[dict], query: str, location: str) -> str:
    """Builds a clean HTML email body."""

    verdict_colors = {
        "STRONG_MATCH": "#22c55e",
        "GOOD_MATCH"  : "#eab308",
        "WEAK_MATCH"  : "#f97316",
        "NO_MATCH"    : "#ef4444"
    }

    job_cards = ""
    for i, job in enumerate(jobs, 1):
        color    = verdict_colors.get(job.get("verdict", ""), "#6b7280")
        missing  = ", ".join(job.get("missing_skills", [])) or "None"
        matching = ", ".join(job.get("matching_skills", []))

        job_cards += f"""
        <div style="border:1px solid #e5e7eb; border-radius:8px;
                    padding:16px; margin-bottom:16px;">
            <h3 style="margin:0 0 8px 0;">
                #{i} {job.get('title', 'N/A')}
            </h3>
            <p style="margin:0 0 4px 0; color:#6b7280;">
                {job.get('company', 'N/A')} — {job.get('location', 'N/A')}
            </p>
            <span style="background:{color}; color:white;
                         padding:2px 8px; border-radius:4px; font-size:12px;">
                {job.get('score', 0)}/10 — {job.get('verdict', 'N/A')}
            </span>
            <p style="margin:8px 0 4px 0;">
                <strong>Matching:</strong> {matching}
            </p>
            <p style="margin:0 0 4px 0;">
                <strong>Missing:</strong> {missing}
            </p>
            <p style="margin:8px 0 0 0;">
                <strong>Reason:</strong> {job.get('reason', 'N/A')}
            </p>
            <a href="{job.get('link', '#')}"
               style="display:inline-block; margin-top:12px;
                      background:#2563eb; color:white;
                      padding:8px 16px; border-radius:6px;
                      text-decoration:none;">
                Apply Now →
            </a>
        </div>
        """

    return f"""
    <html><body style="font-family:sans-serif; max-width:600px; margin:0 auto; padding:20px;">
        <h1 style="color:#1e293b;">🎯 Job Search Results</h1>
        <p style="color:#6b7280;">
            Query: <strong>{query}</strong> in <strong>{location}</strong>
        </p>
        <p style="color:#6b7280;">
            Found <strong>{len(jobs)}</strong> matches
            ({len([j for j in jobs if j.get('score',0) >= 9])} strong)
        </p>
        <hr style="border:none; border-top:1px solid #e5e7eb; margin:20px 0;">
        {job_cards}
        <p style="color:#9ca3af; font-size:12px; margin-top:24px;">
            Sent by your Job Search Agent
        </p>
    </body></html>
    """