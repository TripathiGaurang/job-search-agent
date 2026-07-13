import sys
import os
sys.path.append(os.path.dirname(__file__))

from langgraph.graph import StateGraph, END
from state import AgentState
from agents.fetcher_agent  import fetcher_agent
from agents.scorer_agent   import scorer_agent
from agents.notifier_agent import notifier_agent


def route_after_fetch(state: AgentState) -> str:
    """
    Decision point after Fetcher Agent.
    Reads message set by fetcher and decides next agent.
    """
    message = state["message"]

    if message == "fetch_failed":
        return "notifier"       # go straight to notifier to report error

    if message == "no_new_jobs":
        return "notifier"       # go to notifier to show saved jobs

    return "scorer"             # new jobs found — go score them


def build_graph():
    graph = StateGraph(AgentState)

    # ── Register agents as nodes ───────────────────────────────
    graph.add_node("fetcher",  fetcher_agent)
    graph.add_node("scorer",   scorer_agent)
    graph.add_node("notifier", notifier_agent)

    # ── Entry point ────────────────────────────────────────────
    graph.set_entry_point("fetcher")

    # ── Conditional edge after fetcher ─────────────────────────
    graph.add_conditional_edges(
        "fetcher",
        route_after_fetch,
        {
            "scorer"   : "scorer",
            "notifier" : "notifier"
        }
    )

    # ── Fixed edges ────────────────────────────────────────────
    graph.add_edge("scorer",   "notifier")
    graph.add_edge("notifier", END)

    return graph.compile()