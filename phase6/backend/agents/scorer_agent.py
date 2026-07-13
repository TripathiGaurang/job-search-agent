import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from state import AgentState
from tools.job_scorer import score_job
from memory.db        import save_job
from rag.vector_store import index_job 


async def score_single_job(job: dict, resume: str, index: int, total: int) -> dict:
    """Scores a single job asynchronously."""
    print(f"   ⚡ [{index}/{total}] Scoring: {job['title']} at {job['company']}")
    loop   = asyncio.get_event_loop()
    scored = await loop.run_in_executor(None, score_job, job, resume)
    print(f"   ✅ [{index}/{total}] Done: {scored['title']} → {scored['score']}/10")
    return scored


async def score_all_jobs_parallel(jobs: list, resume: str) -> list:
    """Scores all jobs simultaneously."""
    tasks   = [
        score_single_job(job, resume, i+1, len(jobs))
        for i, job in enumerate(jobs)
    ]
    results = await asyncio.gather(*tasks)
    return list(results)


def scorer_agent(state: AgentState) -> AgentState:
    """
    SCORER AGENT — scores jobs sequentially.
    Simple and reliable inside FastAPI context.
    """
    print("\n" + "="*50)
    print("⚡ SCORER AGENT starting...")
    print("="*50)

    start_time = time.time()
    errors     = list(state.get("errors", []))
    new_jobs   = state["new_jobs"]

    if not new_jobs:
        print("   No new jobs to score.")
        return {**state, "scored_jobs": [], "score_time": 0.0}

    print(f"\n   Scoring {len(new_jobs)} jobs...\n")

    scored_jobs = []
    for i, job in enumerate(new_jobs, 1):
        try:
            print(f"   ⚡ [{i}/{len(new_jobs)}] {job['title']} at {job['company']}")
            scored = score_job(job, state["resume"])
            scored_jobs.append(scored)
            save_job(scored, state["user_email"])
            index_job(scored, state["user_email"])
            print(f"   ✅ Score: {scored['score']}/10 — {scored['verdict']}")
        except Exception as e:
            error_msg = f"Scoring failed for {job['title']}: {str(e)}"
            print(f"   ❌ {error_msg}")
            errors.append(error_msg)

    score_time = time.time() - start_time
    print(f"\n   ⏱️  Scoring done in {score_time:.2f}s")

    return {
        **state,
        "scored_jobs" : scored_jobs,
        "score_time"  : score_time,
        "errors"      : errors
    }