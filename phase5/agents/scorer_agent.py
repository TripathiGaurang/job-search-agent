import sys
import os
import time
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from state import AgentState
from tools.job_scorer import score_job
from memory.db        import save_job


# ─── Async scoring function ───────────────────────────────────────────────────

async def score_single_job(job: dict, resume: str, index: int, total: int) -> dict:
    """
    Scores a single job asynchronously.
    Each call to this runs concurrently with others via asyncio.gather()
    """
    print(f"   ⚡ [{index}/{total}] Scoring: {job['title']} at {job['company']}")

    # Run the synchronous score_job in a thread pool
    # so it doesn't block the event loop
    loop   = asyncio.get_event_loop()
    scored = await loop.run_in_executor(
        None,           # use default thread pool
        score_job,      # function to run
        job,            # argument 1
        resume          # argument 2
    )

    print(f"   ✅ [{index}/{total}] Done: {scored['title']} → {scored['score']}/10")
    return scored


async def score_all_jobs_parallel(jobs: list, resume: str) -> list:
    """
    Scores ALL jobs simultaneously using asyncio.gather().
    All LLM calls fire at the same time instead of one by one.
    """
    tasks = [
        score_single_job(job, resume, i+1, len(jobs))
        for i, job in enumerate(jobs)
    ]
    # This is the magic line — runs all tasks at the same time
    results = await asyncio.gather(*tasks)
    return list(results)


# ─── Scorer Agent Node ────────────────────────────────────────────────────────

def scorer_agent(state: AgentState) -> AgentState:
    """
    SCORER AGENT
    Responsibility: Score all new jobs against resume in parallel.

    Reads : new_jobs, resume
    Writes: scored_jobs, score_time
    """
    print("\n" + "="*50)
    print("⚡ SCORER AGENT starting...")
    print("="*50)

    start_time = time.time()
    errors     = list(state.get("errors", []))

    new_jobs = state["new_jobs"]

    if not new_jobs:
        print("   No new jobs to score.")
        return {
            **state,
            "scored_jobs" : [],
            "score_time"  : 0.0
        }

    print(f"\n   Scoring {len(new_jobs)} jobs in PARALLEL...")
    print(f"   All LLM calls fire simultaneously.\n")

    try:
        # Run parallel scoring
        scored_jobs = asyncio.run(
            score_all_jobs_parallel(new_jobs, state["resume"])
        )

        # Save all scored jobs to database
        print(f"\n💾 Saving {len(scored_jobs)} jobs to database...")
        for job in scored_jobs:
            save_job(job)
        print("   All saved.")

        score_time = time.time() - start_time
        print(f"\n   ⏱️  Scoring completed in {score_time:.2f} seconds")

    except Exception as e:
        error_msg = f"ScorerAgent error: {str(e)}"
        print(f"❌ {error_msg}")
        errors.append(error_msg)
        scored_jobs = []
        score_time  = time.time() - start_time

    return {
        **state,
        "scored_jobs" : scored_jobs,
        "score_time"  : score_time,
        "errors"      : errors
    }