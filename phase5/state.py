from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    """
    Shared state that flows through all agents.
    Every agent reads from and writes to this.
    """
    # Input
    query         : str
    location      : str
    num_jobs      : int

    # Resume
    resume        : str

    # Job data — each agent adds its layer
    fetched_jobs  : List[dict]    # raw from API
    new_jobs      : List[dict]    # after dedup filter
    scored_jobs   : List[dict]    # after LLM scoring

    # Tracking
    skipped_count : int
    errors        : List[str]     # NEW — tracks any errors from any agent

    # Timing — NEW — we'll measure parallel vs sequential speed
    fetch_time    : float
    score_time    : float
    total_time    : float

    # Control
    message       : str