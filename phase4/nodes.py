import sys
import os
sys.path.append(os.path.dirname(__file__))

from state import AgentState
from tools.job_fetcher import fetch_jobs
from tools.job_scorer  import score_job, load_resume
from memory.db         import init_db, is_job_seen, save_job, get_all_jobs


def node_load_resume(state: AgentState) -> AgentState:
    """
    Node 1 — Loads resume from PDF.
    Reads : query, location (already in state)
    Writes: resume
    """
    print("\n📄 [Node] Loading resume...")
    resume = load_resume("../phase1/GaurangTripathiResume.pdf")
    print("   Resume loaded.")

    return {**state, "resume": resume}


def node_fetch_jobs(state: AgentState) -> AgentState:
    """
    Node 2 — Fetches jobs from JSearch API.
    Reads : query, location, num_jobs
    Writes: fetched_jobs
    """
    print(f"\n🔍 [Node] Fetching jobs...")
    jobs = fetch_jobs(state["query"], state["location"], state["num_jobs"])
    print(f"   Found {len(jobs)} jobs from API.")

    return {**state, "fetched_jobs": jobs}


def node_filter_seen(state: AgentState) -> AgentState:
    """
    Node 3 — Filters out already seen jobs using database memory.
    Reads : fetched_jobs
    Writes: new_jobs, skipped_count, message
    """
    print(f"\n🧠 [Node] Checking memory for duplicates...")
    init_db()

    new_jobs = []
    skipped  = 0

    for job in state["fetched_jobs"]:
        if is_job_seen(job["job_id"]):
            skipped += 1
            print(f"   ⏭️  Already seen: {job['title']} at {job['company']}")
        else:
            new_jobs.append(job)

    print(f"   {len(new_jobs)} new, {skipped} skipped.")

    message = f"{len(new_jobs)} new jobs found" if new_jobs else "no_new_jobs"

    return {**state, "new_jobs": new_jobs, "skipped_count": skipped, "message": message}


def node_score_jobs(state: AgentState) -> AgentState:
    """
    Node 4 — Scores each new job against resume using LLM.
    Reads : new_jobs, resume
    Writes: scored_jobs
    """
    print(f"\n⚡ [Node] Scoring {len(state['new_jobs'])} new jobs...")

    scored_jobs = []
    for i, job in enumerate(state["new_jobs"], 1):
        print(f"   Scoring {i}/{len(state['new_jobs'])}: {job['title']}")
        scored = score_job(job, state["resume"])
        scored_jobs.append(scored)

    return {**state, "scored_jobs": scored_jobs}


def node_save_jobs(state: AgentState) -> AgentState:
    """
    Node 5 — Saves scored jobs to database.
    Reads : scored_jobs
    Writes: message (updated)
    """
    print(f"\n💾 [Node] Saving {len(state['scored_jobs'])} jobs to database...")

    for job in state["scored_jobs"]:
        save_job(job)

    print(f"   All jobs saved.")
    return {**state, "message": "jobs_saved"}


def node_display_results(state: AgentState) -> AgentState:
    """
    Node 6 — Displays ranked results.
    Reads : scored_jobs
    Writes: message (final)
    """
    ranked = sorted(state["scored_jobs"], key=lambda x: x["score"], reverse=True)

    print("\n" + "="*60)
    print("🏆 RANKED JOB MATCHES")
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

    return {**state, "message": "complete"}


def node_show_saved(state: AgentState) -> AgentState:
    """
    Node 7 — Shows saved jobs when no new ones found.
    This node is reached via conditional edge — only when message = 'no_new_jobs'
    """
    print("\n✅ No new jobs found. Showing saved jobs from database:\n")

    jobs = get_all_jobs(min_score=6)
    print(f"📂 Saved Jobs (score >= 6):")
    print("="*60)

    for job in jobs:
        print(f"\n{job['title']} at {job['company']}")
        print(f"    Score   : {job['score']}/10 — {job['verdict']}")
        print(f"    Status  : {job['status']}")
        print(f"    Seen at : {job['seen_at']}")
        print(f"    Link    : {job['link']}")

    return {**state, "message": "complete"}