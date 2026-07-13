from typing import TypedDict, List

class AgentState(TypedDict):
    # User info
    user_email    : str
    query         : str
    location      : str
    num_jobs      : int

    # Resume
    resume        : str
    resume_path   : str        # path to uploaded PDF

    # Job data
    fetched_jobs  : List[dict]
    new_jobs      : List[dict]
    scored_jobs   : List[dict]

    # Tracking
    skipped_count : int
    errors        : List[str]
    fetch_time    : float
    score_time    : float
    total_time    : float
    message       : str