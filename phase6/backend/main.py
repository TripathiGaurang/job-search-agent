import os
import sys
import time
import asyncio
import concurrent.futures
import shutil
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

sys.path.append(os.path.dirname(__file__))

from graph import build_graph
from state import AgentState
from memory.db import init_db, get_all_jobs, update_job_status, save_run
from notifications.email_sender import send_job_digest
from rag.vector_store import find_similar_jobs, build_job_text

# ── App Setup ─────────────────────────────────────────────────────────────────

app = FastAPI(title="Job Search Agent API")

# Change the allow_origins array to include your Vercel URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

init_db()

# ── Request/Response Models ───────────────────────────────────────────────────

class StatusUpdate(BaseModel):
    status: str   # "applied" | "rejected" | "seen"

class EmailRequest(BaseModel):
    to_email : str
    query    : str
    location : str

# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "Job Search Agent API is running"}


@app.post("/search")
async def search_jobs(
    email    : str        = Form(...),
    query    : str        = Form(...),
    location : str        = Form(...),
    num_jobs : int        = Form(5),
    resume   : UploadFile = File(...)
):
    resume_path = UPLOAD_DIR / f"{email}_resume.pdf"
    with open(resume_path, "wb") as f:
        shutil.copyfileobj(resume.file, f)

    print(f"\n🚀 Search request from {email}")
    print(f"   Query: {query} in {location}")

    initial_state: AgentState = {
        "user_email"    : email,
        "query"         : query,
        "location"      : location,
        "num_jobs"      : num_jobs,
        "resume"        : "",
        "resume_path"   : str(resume_path),
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

    start       = time.time()
    graph       = build_graph()
    final_state = graph.invoke(initial_state)
    total_time  = time.time() - start

    scored_jobs = final_state.get("scored_jobs", [])

    save_run(
        user_email   = email,
        query        = query,
        location     = location,
        jobs_found   = len(final_state.get("fetched_jobs", [])),
        jobs_new     = len(scored_jobs),
        jobs_skipped = final_state.get("skipped_count", 0)
    )

    if scored_jobs:
        try:
            send_job_digest(email, scored_jobs, query, location)
            print("   ✅ Email digest dispatched successfully.")
        except Exception as email_err:
            # Captures the network block so it doesn't crash the entire API payload return
            print(f"   ⚠️ Email dispatch skipped or network unreachable: {email_err}")

    ranked = sorted(scored_jobs, key=lambda x: x.get("score", 0), reverse=True)

    return JSONResponse({
        "success"    : True,
        "jobs"       : ranked,
        "total_found": len(final_state.get("fetched_jobs", [])),
        "new_jobs"   : len(scored_jobs),
        "skipped"    : final_state.get("skipped_count", 0),
        "fetch_time" : round(final_state.get("fetch_time", 0), 2),
        "score_time" : round(final_state.get("score_time", 0), 2),
        "total_time" : round(total_time, 2),
        "errors"     : final_state.get("errors", [])
    })


@app.get("/jobs/{email}")
def get_saved_jobs(email: str, min_score: int = 0):
    """Returns all saved jobs for a user."""
    jobs = get_all_jobs(user_email=email, min_score=min_score)
    return {"jobs": jobs, "count": len(jobs)}


@app.put("/jobs/{job_id}/status")
def update_status(job_id: str, body: StatusUpdate):
    """Updates job status — applied, rejected, seen."""
    if body.status not in ["applied", "rejected", "seen"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    update_job_status(job_id, body.status)
    return {"success": True, "job_id": job_id, "status": body.status}


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/jobs/{email}/similar")
def get_similar_jobs(
    email : str,
    query : str,
    top_k : int = 5
):
    """
    Semantic search over saved jobs by text query.
    
    Called when user types in the search box.
    Example: GET /jobs/gaurang@gmail.com/similar?query=React SharePoint
    
    Flow:
      1. Convert query to embedding
      2. ChromaDB finds most similar job embeddings
      3. Fetch full details from SQLite
      4. Return combined results
    
    Why fetch from SQLite after ChromaDB?
      ChromaDB has: title, company, score, verdict, link
      SQLite has:   all of the above PLUS status, seen_at, reason
      We use ChromaDB to FIND jobs
      SQLite to GET full details
    """
    if not query:
        raise HTTPException(
            status_code = 400,
            detail      = "Query parameter is required"
        )

    # Step 1 — Find similar job IDs from ChromaDB
    similar = find_similar_jobs(
        query_text = query,
        user_email = email,
        top_k      = top_k
    )

    if not similar:
        return {"jobs": [], "query": query, "count": 0}

    # Step 2 — Get full details from SQLite
    all_saved  = get_all_jobs(user_email=email)

    # Build lookup dictionary for fast access
    # { job_id → full job dict }
    # O(1) lookup instead of O(n) loop for each result
    job_lookup = {job["job_id"]: job for job in all_saved}

    # Step 3 — Combine ChromaDB similarity with SQLite details
    enriched = []
    for s in similar:
        job_id = s["job_id"]
        if job_id in job_lookup:
            full_job               = job_lookup[job_id].copy()
            full_job["similarity"] = s["similarity"]
            enriched.append(full_job)

    return {
        "jobs"  : enriched,
        "query" : query,
        "count" : len(enriched)
    }


@app.get("/jobs/{email}/similar-to/{job_id}")
def get_jobs_similar_to(
    email  : str,
    job_id : str,
    top_k  : int = 5
):
    """
    Finds jobs similar to a SPECIFIC saved job.
    
    Called when user clicks "Find Similar" button on a job card.
    Example: GET /jobs/gaurang@gmail.com/similar-to/abc123
    
    Difference from /similar endpoint:
      /similar      → user provides TEXT query
      /similar-to   → user provides a JOB ID
                      we build the query from that job's content
                      and exclude it from results
    """
    # Get full job details from SQLite
    all_saved  = get_all_jobs(user_email=email)
    job_lookup = {job["job_id"]: job for job in all_saved}

    if job_id not in job_lookup:
        raise HTTPException(
            status_code = 404,
            detail      = f"Job {job_id} not found"
        )

    source_job = job_lookup[job_id]

    # Build query text from source job
    query_text = build_job_text(source_job)

    # Find similar — excluding source job itself
    similar = find_similar_jobs(
        query_text = query_text,
        user_email = email,
        top_k      = top_k,
        exclude_id = job_id
    )

    if not similar:
        return {
            "source_job": source_job,
            "similar"   : [],
            "count"     : 0
        }

    # Enrich with full SQLite details
    enriched = []
    for s in similar:
        if s["job_id"] in job_lookup:
            full               = job_lookup[s["job_id"]].copy()
            full["similarity"] = s["similarity"]
            enriched.append(full)

    return {
        "source_job": source_job,
        "similar"   : enriched,
        "count"     : len(enriched)
    }