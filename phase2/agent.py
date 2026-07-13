from tools.job_fetcher import fetch_jobs
from tools.job_scorer  import score_job, load_resume

def run_agent(query: str, location: str, num_jobs: int = 5):
    """
    The Job Search Agent.
    Step 1: Fetch jobs
    Step 2: Score each job against resume
    Step 3: Rank and display results
    """
    print(f"\n🤖 Agent starting...")
    print(f"   Query    : {query}")
    print(f"   Location : {location}\n")

    # --- Step 1: Load resume once ---
    print("📄 Loading resume...")
    resume = load_resume("../phase1/GaurangTripathiResume.pdf")

    # --- Step 2: Fetch jobs ---
    print(f"🔍 Fetching jobs...")
    jobs = fetch_jobs(query, location, num_jobs)
    print(f"   Found {len(jobs)} jobs\n")

    if not jobs:
        print("No jobs found. Try a different query.")
        return

    # --- Step 3: Score each job ---
    print("⚡ Scoring jobs against your resume...\n")
    scored_jobs = []
    for i, job in enumerate(jobs, 1):
        print(f"   Scoring job {i}/{len(jobs)}: {job['title']} at {job['company']}")
        scored = score_job(job, resume)
        scored_jobs.append(scored)

    # --- Step 4: Rank by score ---
    ranked_jobs = sorted(scored_jobs, key=lambda x: x["score"], reverse=True)

    # --- Step 5: Display results ---
    print("\n" + "="*60)
    print("🏆 RANKED JOB MATCHES")
    print("="*60)

    for i, job in enumerate(ranked_jobs, 1):
        print(f"\n#{i} {job['title']} at {job['company']}")
        print(f"    Score    : {job['score']}/10 — {job['verdict']}")
        print(f"    Source   : {job['source']}")
        print(f"    Matching : {', '.join(job['matching_skills'])}")
        print(f"    Missing  : {', '.join(job['missing_skills']) or 'None'}")
        print(f"    Reason   : {job['reason']}")
        print(f"    Link     : {job['link']}")

    print("\n" + "="*60)
    print(f"✅ Agent complete. {len(ranked_jobs)} jobs ranked.")


if __name__ == "__main__":
    run_agent(
        query    = "SharePoint Developer",
        location = "Gurugram"
    )