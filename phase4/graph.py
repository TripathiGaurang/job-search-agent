import sys
import os
sys.path.append(os.path.dirname(__file__))

from langgraph.graph import StateGraph, END
from state import AgentState
from nodes import (
    node_load_resume,
    node_fetch_jobs,
    node_filter_seen,
    node_score_jobs,
    node_save_jobs,
    node_display_results,
    node_show_saved
)

def should_score_or_show_saved(state: AgentState) -> str:
    """
    Conditional edge — the decision point.
    LangGraph calls this after node_filter_seen.
    Returns the name of the next node to go to.
    """
    if state["message"] == "no_new_jobs":
        return "show_saved"     # → go to node_show_saved
    else:
        return "score_jobs"     # → go to node_score_jobs


def build_graph():
    """Builds and compiles the agent graph."""

    # 1. Create the graph with our state type
    graph = StateGraph(AgentState)

    # 2. Add all nodes
    graph.add_node("load_resume",     node_load_resume)
    graph.add_node("fetch_jobs",      node_fetch_jobs)
    graph.add_node("filter_seen",     node_filter_seen)
    graph.add_node("score_jobs",      node_score_jobs)
    graph.add_node("save_jobs",       node_save_jobs)
    graph.add_node("display_results", node_display_results)
    graph.add_node("show_saved",      node_show_saved)

    # 3. Add edges — the fixed paths
    graph.add_edge("load_resume",     "fetch_jobs")
    graph.add_edge("fetch_jobs",      "filter_seen")
    graph.add_edge("score_jobs",      "save_jobs")
    graph.add_edge("save_jobs",       "display_results")
    graph.add_edge("display_results", END)
    graph.add_edge("show_saved",      END)

    # 4. Add conditional edge — the decision point
    graph.add_conditional_edges(
        "filter_seen",              # after this node
        should_score_or_show_saved, # call this function to decide
        {
            "score_jobs"  : "score_jobs",   # if returns "score_jobs"  → go here
            "show_saved"  : "show_saved"    # if returns "show_saved"  → go here
        }
    )

    # 5. Set the entry point
    graph.set_entry_point("load_resume")

    # 6. Compile and return
    return graph.compile()