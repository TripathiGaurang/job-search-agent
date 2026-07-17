import sys
import os
import time
import concurrent.futures
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from state import AgentState
from tools.job_scorer import score_job
from memory.db        import save_job
from rag.vector_store import index_job


def _score_single_job(args):
    """
    Scores one job — runs inside a thread.
    Takes args as tuple because ThreadPoolExecutor.map
    only passes one argument per call.
    """
    job, resume, user_email, index, total = args
    try:
        print(f"   ⚡ [{index}/{total}] Scoring: {job['title']} at {job['company']}")
        scored = score_job(job, resume)
        save_job(scored, user_email)
        index_job(scored, user_email)
        print(f"   ✅ [{index}/{total}] Done: {scored['title']} → {scored['score']}/10")
        return scored
    except Exception as e:
        print(f"   ❌ [{index}/{total}] Failed: {job.get('title')} — {str(e)}")
        return None


def scorer_agent(state: AgentState) -> AgentState:
    """
    SCORER AGENT
    Scores all new jobs in parallel using ThreadPoolExecutor.
    All LLM calls fire simultaneously instead of one by one.
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

    print(f"\n   Scoring {len(new_jobs)} jobs in PARALLEL...\n")

    # Build args list — one tuple per job
    # ThreadPoolExecutor.map calls _score_single_job(args)
    # for each item in this list simultaneously
    args_list = [
        (job, state["resume"], state["user_email"], i+1, len(new_jobs))
        for i, job in enumerate(new_jobs)
    ]

    # max_workers=5 means up to 5 LLM calls run at the same time
    # If you have 3 jobs → 3 threads, all fire simultaneously
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(_score_single_job, args_list))

    # Filter out None results from any failed jobs
    scored_jobs = [r for r in results if r is not None]

    score_time = time.time() - start_time
    print(f"\n   ⏱️  Scoring completed in {score_time:.2f}s")
    print(f"   Scored {len(scored_jobs)}/{len(new_jobs)} jobs successfully")

    return {
        **state,
        "scored_jobs" : scored_jobs,
        "score_time"  : score_time,
        "errors"      : errors
    }