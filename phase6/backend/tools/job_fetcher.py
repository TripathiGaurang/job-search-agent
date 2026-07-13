import os
import requests
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")


def fetch_from_jsearch(query: str, location: str, num_jobs: int = 5, page: str = "1") -> list:
    url     = "https://jsearch.p.rapidapi.com/search-v2"
    headers = {
        "x-rapidapi-key"  : RAPIDAPI_KEY,
        "x-rapidapi-host" : "jsearch.p.rapidapi.com"
    }
    params = {
        "query"       : f"{query} in {location}",
        "page"        : page,
        "num_pages"   : "1",
        "date_posted" : "month",
        "country"     : "in"
    }
    try:
        response  = requests.get(url, headers=headers, params=params, timeout=15)
        data      = response.json()
        jobs_list = data.get("data", {}).get("jobs", [])
        result    = [_normalise(job) for job in jobs_list[:num_jobs]]
        print(f"   ✅ JSearch page {page}: {len(result)} jobs")
        return result
    except Exception as e:
        print(f"   ⚠️ JSearch page {page} failed: {e}")
        return []


def _normalise(job: dict) -> dict:
    return {
        "job_id"  : job.get("job_id", ""),
        "title"   : job.get("job_title", "N/A"),
        "company" : job.get("employer_name", "N/A"),
        "location": job.get("job_city", "N/A"),
        "summary" : job.get("job_description", "")[:600],
        "link"    : job.get("job_apply_link", "N/A"),
        "source"  : job.get("job_publisher", "JSearch")
    }


def fetch_jobs(query: str, location: str, num_jobs: int = 5) -> list:
    """
    Fetches from JSearch across 2 pages for more results.
    Deduplicates by job_id before returning.
    """
    print(f"   🔎 Fetching jobs from JSearch...")
    all_jobs = []

    all_jobs.extend(fetch_from_jsearch(query, location, num_jobs, page="1"))
    all_jobs.extend(fetch_from_jsearch(query, location, num_jobs, page="2"))

    # Deduplicate
    seen_ids    = set()
    unique_jobs = []
    for job in all_jobs:
        if job["job_id"] and job["job_id"] not in seen_ids:
            seen_ids.add(job["job_id"])
            unique_jobs.append(job)

    print(f"   📊 Total unique jobs: {len(unique_jobs)}")
    return unique_jobs