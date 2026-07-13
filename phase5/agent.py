import sys
import os
import time
sys.path.append(os.path.dirname(__file__))

from graph import build_graph

def run_agent(query: str, location: str, num_jobs: int = 5):

    print(f"\n{'='*60}")
    print("🤖 MULTI-AGENT JOB SEARCH SYSTEM")
    print(f"{'='*60}")
    print(f"   Query    : {query}")
    print(f"   Location : {location}")
    print(f"   Agents   : Fetcher → Scorer (parallel) → Notifier")

    app = build_graph()

    initial_state = {
        "query"         : query,
        "location"      : location,
        "num_jobs"      : num_jobs,
        "resume"        : "",
        "fetched_jobs"  : [],
        "new_jobs"      : [],
        "scored_jobs"   : [],
        "skipped_count" : 0,
        "errors"        : [],
        "fetch_time"    : 0.0,
        "score_time"    : 0.0,
        "total_time"    : 0.0,
        "message"       : ""
    }

    start = time.time()
    app.invoke(initial_state)
    print(f"\n✅ Total wall time: {time.time() - start:.2f}s")


if __name__ == "__main__":
    run_agent(
        query    = "SharePoint Developer",
        location = "Gurugram"
    )