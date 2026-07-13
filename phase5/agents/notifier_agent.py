import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from state import AgentState
from memory.db import get_all_jobs


def notifier_agent(state: AgentState) -> AgentState:
    """
    NOTIFIER AGENT
    Responsibility: Format and display final ranked results.
    In Phase 6 this becomes the email sender.

    Reads : scored_jobs, message, errors, fetch_time, score_time
    Writes: total_time, message
    """
    print("\n" + "="*50)
    print("📢 NOTIFIER AGENT starting...")
    print("="*50)

    start_time = time.time()

    # ── Case 1: No new jobs found ──────────────────────────────
    if state["message"] == "no_new_jobs":
        print("\n✅ No new jobs this run. Showing your saved history:\n")
        _show_saved_jobs()
        total_time = time.time() - start_time
        return {**state, "total_time": total_time, "message": "complete"}

    # ── Case 2: Fetch failed ───────────────────────────────────
    if state["message"] == "fetch_failed":
        print("\n❌ Job fetch failed. Check your API key and connection.")
        _show_errors(state["errors"])
        total_time = time.time() - start_time
        return {**state, "total_time": total_time, "message": "failed"}

    # ── Case 3: Scored jobs to display ────────────────────────
    scored_jobs = state.get("scored_jobs", [])

    if not scored_jobs:
        print("\n⚠️ No jobs were scored this run.")
        total_time = time.time() - start_time
        return {**state, "total_time": total_time, "message": "complete"}

    # Rank by score
    ranked = sorted(scored_jobs, key=lambda x: x["score"], reverse=True)

    print(f"\n{'='*60}")
    print("🏆 RANKED JOB MATCHES")
    print(f"{'='*60}")

    for i, job in enumerate(ranked, 1):
        verdict_emoji = {
            "STRONG_MATCH" : "🟢",
            "GOOD_MATCH"   : "🟡",
            "WEAK_MATCH"   : "🟠",
            "NO_MATCH"     : "🔴"
        }.get(job["verdict"], "⚪")

        print(f"\n#{i} {job['title']}")
        print(f"    Company  : {job['company']}")
        print(f"    Score    : {job['score']}/10 {verdict_emoji} {job['verdict']}")
        print(f"    Source   : {job['source']}")
        print(f"    Matching : {', '.join(job.get('matching_skills', []))}")
        print(f"    Missing  : {', '.join(job.get('missing_skills', [])) or 'None'}")
        print(f"    Reason   : {job['reason']}")
        print(f"    Link     : {job['link']}")

    # ── Performance Summary ────────────────────────────────────
    total_time = time.time() - start_time
    full_total = state.get("fetch_time", 0) + state.get("score_time", 0) + total_time

    print(f"\n{'='*60}")
    print("📊 PERFORMANCE SUMMARY")
    print(f"{'='*60}")
    print(f"   Jobs fetched     : {len(state['fetched_jobs'])}")
    print(f"   New jobs scored  : {len(scored_jobs)}")
    print(f"   Jobs skipped     : {state['skipped_count']}")
    print(f"   Fetch time       : {state.get('fetch_time', 0):.2f}s")
    print(f"   Score time       : {state.get('score_time', 0):.2f}s  ← parallel")
    print(f"   Total time       : {full_total:.2f}s")

    if state["errors"]:
        _show_errors(state["errors"])

    return {
        **state,
        "total_time" : total_time,
        "message"    : "complete"
    }


def _show_saved_jobs():
    """Private helper — shows jobs from database."""
    jobs = get_all_jobs(min_score=6)
    if not jobs:
        print("   No saved jobs found yet.")
        return

    print(f"{'='*60}")
    for job in jobs:
        print(f"\n{job['title']} at {job['company']}")
        print(f"    Score   : {job['score']}/10 — {job['verdict']}")
        print(f"    Status  : {job['status']}")
        print(f"    Seen at : {job['seen_at']}")
        print(f"    Link    : {job['link']}")


def _show_errors(errors: list):
    """Private helper — shows any errors that occurred."""
    print(f"\n⚠️ Errors encountered:")
    for err in errors:
        print(f"   • {err}")