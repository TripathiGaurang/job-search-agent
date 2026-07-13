import sys
import os
sys.path.append(os.path.dirname(__file__))

from graph import build_graph

def run_agent(query: str, location: str, num_jobs: int = 5):
    print(f"\n🤖 LangGraph Agent starting...")
    print(f"   Query    : {query}")
    print(f"   Location : {location}")

    # Build the graph
    app = build_graph()

    # Initial state — this is what gets passed to the first node
    initial_state = {
        "query"         : query,
        "location"      : location,
        "num_jobs"      : num_jobs,
        "resume"        : "",
        "fetched_jobs"  : [],
        "new_jobs"      : [],
        "scored_jobs"   : [],
        "skipped_count" : 0,
        "message"       : ""
    }

    # Run the graph
    app.invoke(initial_state)


if __name__ == "__main__":
    run_agent(
        query    = "SharePoint Developer",
        location = "Gurugram"
    )