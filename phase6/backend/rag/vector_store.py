import os
import chromadb
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from rag.embedder import get_embedding

IS_RENDER = os.getenv("RENDER") is not None

if IS_RENDER:
    CHROMA_PATH = "/tmp/chroma_db"
else:
    CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")


def build_job_text(job: dict) -> str:
    """
    Builds a single rich text string from job fields.
    This is what gets converted to an embedding.
    """
    parts = [
        f"Job Title: {job.get('title', '')}",
        f"Company: {job.get('company', '')}",
        f"Description: {job.get('summary', '')}",
    ]

    matching = job.get("matching_skills", [])
    missing  = job.get("missing_skills", [])

    if matching:
        parts.append(f"Matching skills: {', '.join(matching)}")
    if missing:
        parts.append(f"Required skills: {', '.join(missing)}")

    return "\n".join(parts)

def index_job(job: dict, user_email: str):
    """
    Stores a job's embedding in ChromaDB.
    Called once when a job is scored and saved.
    """
    collection = get_collection(user_email)

    # Build rich text from job fields
    job_text  = build_job_text(job)

    # Convert to embedding — one API call
    embedding = get_embedding(job_text)

    # Store in ChromaDB
    collection.upsert(
        ids        = [job["job_id"]],
        embeddings = [embedding],
        documents  = [job_text],
        metadatas  = [{
            "title"  : job.get("title", ""),
            "company": job.get("company", ""),
            "score"  : str(job.get("score", 0)),
            "verdict": job.get("verdict", ""),
            "link"   : job.get("link", "")
        }]
    )

    print(f"   📌 Indexed: {job.get('title')}")

def get_collection(user_email: str):
    """
    Gets or creates a ChromaDB collection for a specific user.
    """
    # Sanitise email — ChromaDB names can't contain @ or .
    # "gaurang@gmail.com" → "gaurang_gmail_com"
    safe_name       = user_email.replace("@", "_").replace(".", "_")
    collection_name = f"{safe_name}_jobs"

    # PersistentClient = saves data to disk
    # Data survives between Python sessions
    # Same concept as SQLite's .db file
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # get_or_create_collection:
    # → collection exists: return it
    # → collection missing: create empty one
    # Safe to call multiple times — never overwrites data
    return client.get_or_create_collection(
        name     = collection_name,
        metadata = {"hnsw:space": "cosine"}
        # hnsw:space = "cosine" tells ChromaDB to use
        # cosine similarity for comparisons
        # This is the same formula we wrote manually
        # in embedder.py — ChromaDB now does it internally
    )


def find_similar_jobs(
    query_text : str,
    user_email : str,
    top_k      : int = 5,
    exclude_id : str = None
) -> list[dict]:
    """
    Finds jobs semantically similar to a query.
    Returns list of dicts with job_id and similarity score.
    """
    collection = get_collection(user_email)

    # Nothing to search if no jobs indexed yet
    if collection.count() == 0:
        print("   ⚠️ No jobs indexed yet")
        return []

    # How many to fetch — extra one if we're excluding a job
    n_results = min(
        top_k + (1 if exclude_id else 0),
        collection.count()
    )

    # Convert query to embedding
    query_embedding = get_embedding(query_text)

    # Ask ChromaDB to find most similar stored embeddings
    results = collection.query(
        query_embeddings = [query_embedding],
        n_results        = n_results
    )

    # Unpack results
    ids       = results["ids"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]

    similar_jobs = []

    for job_id, distance, metadata in zip(ids, distances, metadatas):

        # Skip the source job if searching "similar to THIS job"
        if exclude_id and job_id == exclude_id:
            continue

        # Convert distance to similarity percentage
        # ChromaDB returns cosine DISTANCE (0 = identical, 2 = opposite)
        # We want similarity (1 = identical, 0 = opposite)
        similarity = round((1 - distance) * 100, 1)

        similar_jobs.append({
            "job_id"    : job_id,
            "similarity": similarity,
            "title"     : metadata.get("title", ""),
            "company"   : metadata.get("company", ""),
            "score"     : int(metadata.get("score", "0")),
            "verdict"   : metadata.get("verdict", ""),
            "link"      : metadata.get("link", "")
        })

    # Sort by similarity descending — most similar first
    similar_jobs.sort(key=lambda x: x["similarity"], reverse=True)

    return similar_jobs[:top_k]


if __name__ == "__main__":
    print("Testing vector store...\n")

    # Sample jobs to index
    test_jobs = [
        {
            "job_id"          : "job_001",
            "title"           : "SharePoint React Developer",
            "company"         : "NR Consulting",
            "summary"         : "SPFx developer with React TypeScript experience",
            "matching_skills" : ["SharePoint", "React", "TypeScript"],
            "missing_skills"  : [],
            "score"           : 9,
            "verdict"         : "STRONG_MATCH",
            "link"            : "https://example.com/1"
        },
        {
            "job_id"          : "job_002",
            "title"           : "SPFx Solution Engineer",
            "company"         : "Hollister",
            "summary"         : "SharePoint Online SPFx development Power Platform",
            "matching_skills" : ["SharePoint", "SPFx", "Power Platform"],
            "missing_skills"  : ["DevOps"],
            "score"           : 8,
            "verdict"         : "GOOD_MATCH",
            "link"            : "https://example.com/2"
        },
        {
            "job_id"          : "job_003",
            "title"           : "Java Spring Boot Developer",
            "company"         : "Tech Corp",
            "summary"         : "Java backend developer Spring Boot Microservices",
            "matching_skills" : [],
            "missing_skills"  : ["Java", "Spring Boot"],
            "score"           : 2,
            "verdict"         : "NO_MATCH",
            "link"            : "https://example.com/3"
        }
    ]

    # Step 1 — Index all jobs
    print("Step 1: Indexing jobs...")
    for job in test_jobs:
        index_job(job, "test@example.com")

    # Step 2 — Search by text query
    print("\nStep 2: Searching for 'React SharePoint developer'...")
    results = find_similar_jobs(
        query_text = "React SharePoint developer",
        user_email = "test@example.com",
        top_k      = 3
    )

    print("\nResults:")
    for r in results:
        print(f"  {r['title']} at {r['company']} → {r['similarity']}% similar")

    # Step 3 — Find similar to a specific job
    print("\nStep 3: Finding jobs similar to job_001...")
    similar = find_similar_jobs(
        query_text = build_job_text(test_jobs[0]),
        user_email = "test@example.com",
        top_k      = 2,
        exclude_id = "job_001"
    )

    print("\nSimilar to SharePoint React Developer:")
    for r in similar:
        print(f"  {r['title']} at {r['company']} → {r['similarity']}% similar")