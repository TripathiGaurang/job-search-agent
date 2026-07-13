import sys
import os

# Make sure Python can find our modules
sys.path.append(os.path.dirname(__file__))

from tools.job_fetcher import fetch_jobs
from tools.job_scorer  import score_job, load_resume
from memory.db         import init_db, is_job_seen, save_job, get_all_jobs

def run_agent(query: str, location: str, num_jobs: int = 5):
    """
    Job Search Agent with Memory.
    - Fetches jobs from internet
    - Skips jobs already seen (deduplication)
    - Scores only NEW jobs
    - Saves everything to database
    - Shows ranked results
    """

    print(f"\n🤖 Agent starting...")
    print(f"   Query    : {query}")
    print(f"   Location : {location}\n")

    # --- Step 1: Initialize database ---
    init_db()

    # --- Step 2: Load resume once ---
    print("📄 Loading resume...")
    resume = load_resume("../phase1/GaurangTripathiResume.pdf")
    print("   Resume loaded.\n")

    # --- Step 3: Fetch jobs ---
    print(f"🔍 Fetching jobs from internet...")
    jobs = fetch_jobs(query, location, num_jobs)
    print(f"   Found {len(jobs)} jobs\n")

    if not jobs:
        print("No jobs found. Try a different query.")
        return

    # --- Step 4: Filter out already seen jobs ---
    new_jobs = []
    skipped  = 0

    for job in jobs:
        if is_job_seen(job["job_id"]):
            skipped += 1
            print(f"   ⏭️  Skipping (already seen): {job['title']} at {job['company']}")
        else:
            new_jobs.append(job)

    print(f"\n   {len(new_jobs)} new jobs to process, {skipped} already seen\n")

    if not new_jobs:
        print("✅ No new jobs found. You're up to date!")
        print("\nShowing your saved jobs from database instead:\n")
        show_saved_jobs()
        return

    # --- Step 5: Score only NEW jobs ---
    print("⚡ Scoring new jobs against your resume...\n")
    scored_jobs = []

    for i, job in enumerate(new_jobs, 1):
        print(f"   Scoring {i}/{len(new_jobs)}: {job['title']} at {job['company']}")
        scored = score_job(job, resume)
        scored_jobs.append(scored)

        # Save to database immediately after scoring
        save_job(scored)
        print(f"   💾 Saved to database\n")

    # --- Step 6: Rank and display ---
    ranked = sorted(scored_jobs, key=lambda x: x["score"], reverse=True)

    print("\n" + "="*60)
    print("🏆 RANKED NEW JOB MATCHES")
    print("="*60)

    for i, job in enumerate(ranked, 1):
        print(f"\n#{i} {job['title']} at {job['company']}")
        print(f"    Score    : {job['score']}/10 — {job['verdict']}")
        print(f"    Source   : {job['source']}")
        print(f"    Matching : {', '.join(job['matching_skills'])}")
        print(f"    Missing  : {', '.join(job['missing_skills']) or 'None'}")
        print(f"    Reason   : {job['reason']}")
        print(f"    Link     : {job['link']}")

    print("\n" + "="*60)
    print(f"✅ Done. {len(ranked)} new jobs scored and saved.")
    print(f"   Run again to check for newer listings.")


def show_saved_jobs(min_score: int = 6):
    """Shows all saved jobs from database with score >= min_score."""
    jobs = get_all_jobs(min_score=min_score)

    if not jobs:
        print("No saved jobs found.")
        return

    print(f"\n📂 Saved Jobs (score >= {min_score}):")
    print("="*60)

    for job in jobs:
        print(f"\n{job['title']} at {job['company']}")
        print(f"    Score   : {job['score']}/10 — {job['verdict']}")
        print(f"    Status  : {job['status']}")
        print(f"    Seen at : {job['seen_at']}")
        print(f"    Link    : {job['link']}")


if __name__ == "__main__":
    run_agent(
        query    = "SharePoint Developer",
        location = "Gurugram"
    )