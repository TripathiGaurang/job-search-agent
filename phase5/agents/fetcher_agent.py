import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from state import AgentState
from tools.job_fetcher import fetch_jobs
from tools.job_scorer  import load_resume
from memory.db         import init_db, is_job_seen


def fetcher_agent(state: AgentState) -> AgentState:
    """
    FETCHER AGENT
    Responsibility: Get new jobs from internet, filter already seen ones.

    Reads : query, location, num_jobs
    Writes: fetched_jobs, new_jobs, skipped_count, resume, fetch_time
    """
    print("\n" + "="*50)
    print("🔍 FETCHER AGENT starting...")
    print("="*50)

    start_time = time.time()
    errors = list(state.get("errors", []))

    try:
        # 1. Load resume
        print("📄 Loading resume...")
        resume = load_resume("../phase1/GaurangTripathiResume.pdf")
        print("   Resume loaded.")

        # 2. Fetch jobs from API
        print(f"\n🌐 Fetching jobs: '{state['query']}' in '{state['location']}'")
        jobs = fetch_jobs(state["query"], state["location"], state["num_jobs"])
        print(f"   API returned {len(jobs)} jobs.")

        # 3. Filter already seen jobs
        print("\n🧠 Checking memory for duplicates...")
        init_db()
        new_jobs = []
        skipped  = 0

        for job in jobs:
            if is_job_seen(job["job_id"]):
                skipped += 1
                print(f"   ⏭️  Seen: {job['title']} at {job['company']}")
            else:
                new_jobs.append(job)
                print(f"   ✅ New: {job['title']} at {job['company']}")

        print(f"\n   Result: {len(new_jobs)} new, {skipped} already seen.")

        fetch_time = time.time() - start_time
        message    = "no_new_jobs" if not new_jobs else f"{len(new_jobs)}_new_jobs"

    except Exception as e:
        error_msg = f"FetcherAgent error: {str(e)}"
        print(f"❌ {error_msg}")
        errors.append(error_msg)
        resume     = state.get("resume", "")
        jobs       = []
        new_jobs   = []
        skipped    = 0
        fetch_time = time.time() - start_time
        message    = "fetch_failed"

    return {
        **state,
        "resume"        : resume,
        "fetched_jobs"  : jobs,
        "new_jobs"      : new_jobs,
        "skipped_count" : skipped,
        "fetch_time"    : fetch_time,
        "errors"        : errors,
        "message"       : message
    }