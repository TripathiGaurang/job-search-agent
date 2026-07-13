from typing import TypedDict, List

class AgentState(TypedDict):
    """
    The shared state that flows through every node in our graph.
    Every node can read any field and update any field.
    """
    # Input
    query       : str          # "SharePoint Developer"
    location    : str          # "Gurugram"
    num_jobs    : int          # 5

    # Resume
    resume      : str          # full resume text extracted from PDF

    # Job data
    fetched_jobs : List[dict]  # raw jobs from API
    new_jobs     : List[dict]  # jobs not seen before
    scored_jobs  : List[dict]  # jobs with scores added

    # Control
    skipped_count : int        # how many jobs were skipped
    message       : str        # status message for display