import os
import requests
import asyncio
import feedparser
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# ── Source 1: JSearch API (LinkedIn + Indeed + Glassdoor) ────────────────────

def fetch_from_jsearch(query: str, location: str, num_jobs: int = 5) -> list[dict]:
    """Fetches from JSearch — aggregates LinkedIn, Indeed, Glassdoor."""
    url = "https://jsearch.p.rapidapi.com/search-v2"
    headers = {
        "x-rapidapi-key"  : RAPIDAPI_KEY,
        "x-rapidapi-host" : "jsearch.p.rapidapi.com"
    }
    params = {
        "query"       : f"{query} in {location}",
        "num_pages"   : "1",
        "date_posted" : "month",
        "country"     : "in"
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        data     = response.json()
        jobs_list = data.get("data", {}).get("jobs", [])
        return [_normalise_jsearch(job) for job in jobs_list[:num_jobs]]
    except Exception as e:
        print(f"❌ JSearch error: {e}")
        return []

def _normalise_jsearch(job: dict) -> dict:
    return {
        "job_id"  : job.get("job_id", ""),
        "title"   : job.get("job_title", "N/A"),
        "company" : job.get("employer_name", "N/A"),
        "location": job.get("job_city", "N/A"),
        "summary" : job.get("job_description", "")[:600],
        "link"    : job.get("job_apply_link", "N/A"),
        "source"  : job.get("job_publisher", "JSearch")
    }


# ── Source 2: Naukri RSS ─────────────────────────────────────────────────────

def fetch_from_naukri(query: str, location: str, num_jobs: int = 5) -> list[dict]:
    """Fetches from Naukri via RSS feed."""
    query_fmt    = query.replace(" ", "-").lower()
    location_fmt = location.lower()
    url = f"https://www.naukri.com/rss/jobsearch/{query_fmt}-jobs-in-{location_fmt}"

    try:
        feed = feedparser.parse(url)
        jobs = []
        for entry in feed.entries[:num_jobs]:
            jobs.append({
                "job_id"  : entry.get("link", "")[-20:],
                "title"   : entry.get("title", "N/A"),
                "company" : entry.get("author", "N/A"),
                "location": location,
                "summary" : entry.get("summary", "")[:600],
                "link"    : entry.get("link", "N/A"),
                "source"  : "Naukri"
            })
        return jobs
    except Exception as e:
        print(f"❌ Naukri RSS error: {e}")
        return []


# ── Source 3: TimesJobs RSS ──────────────────────────────────────────────────

def fetch_from_timesjobs(query: str, location: str, num_jobs: int = 5) -> list[dict]:
    """Fetches from TimesJobs via RSS feed."""
    query_fmt = query.replace(" ", "%20")
    url = f"https://www.timesjobs.com/candidate/job-search.html?searchType=personalizedSearch&from=submit&txtKeywords={query_fmt}&txtLocation={location}"

    try:
        feed = feedparser.parse(
            f"https://www.timesjobs.com/jobfeed/rss?query={query_fmt}&location={location}"
        )
        jobs = []
        for entry in feed.entries[:num_jobs]:
            jobs.append({
                "job_id"  : entry.get("id", entry.get("link", ""))[-20:],
                "title"   : entry.get("title", "N/A"),
                "company" : entry.get("author", "N/A"),
                "location": location,
                "summary" : entry.get("summary", "")[:600],
                "link"    : entry.get("link", "N/A"),
                "source"  : "TimesJobs"
            })
        return jobs
    except Exception as e:
        print(f"❌ TimesJobs error: {e}")
        return []


# ── Source 4: RemoteOK API ───────────────────────────────────────────────────

def fetch_from_remoteok(query: str, num_jobs: int = 5) -> list[dict]:
    """Fetches remote jobs from RemoteOK — free public API."""
    try:
        url      = f"https://remoteok.com/api?tag={query.replace(' ', '+')}"
        headers  = {"User-Agent": "JobSearchAgent/1.0"}
        response = requests.get(url, headers=headers, timeout=10)
        data     = response.json()

        jobs = []
        for job in data[1:num_jobs+1]:  # first item is metadata
            jobs.append({
                "job_id"  : str(job.get("id", "")),
                "title"   : job.get("position", "N/A"),
                "company" : job.get("company", "N/A"),
                "location": "Remote",
                "summary" : job.get("description", "")[:600],
                "link"    : job.get("url", "N/A"),
                "source"  : "RemoteOK"
            })
        return jobs
    except Exception as e:
        print(f"❌ RemoteOK error: {e}")
        return []


# ── Main: Fetch from ALL sources in parallel ─────────────────────────────────

async def fetch_from_source_async(source_fn, *args) -> list[dict]:
    """Runs a synchronous fetch function in thread pool asynchronously."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, source_fn, *args)


async def fetch_all_sources_parallel(query: str, location: str, num_jobs: int = 5) -> list[dict]:
    """
    Fetches from all 4 sources simultaneously.
    Merges results and deduplicates by job_id.
    """
    print("   Fetching from 4 sources in parallel...")

    # All 4 sources fire at the same time
    results = await asyncio.gather(
        fetch_from_source_async(fetch_from_jsearch,   query, location, num_jobs),
        fetch_from_source_async(fetch_from_naukri,    query, location, num_jobs),
        fetch_from_source_async(fetch_from_timesjobs, query, location, num_jobs),
        fetch_from_source_async(fetch_from_remoteok,  query, num_jobs),
        return_exceptions=True   # don't crash if one source fails
    )

    # Merge all results
    all_jobs = []
    sources  = ["JSearch", "Naukri", "TimesJobs", "RemoteOK"]
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"   ⚠️ {sources[i]} failed: {result}")
        else:
            print(f"   ✅ {sources[i]}: {len(result)} jobs")
            all_jobs.extend(result)

    # Deduplicate by job_id
    seen_ids  = set()
    unique_jobs = []
    for job in all_jobs:
        if job["job_id"] and job["job_id"] not in seen_ids:
            seen_ids.add(job["job_id"])
            unique_jobs.append(job)

    print(f"   📊 Total unique jobs: {len(unique_jobs)}")
    return unique_jobs


def fetch_jobs(query: str, location: str, num_jobs: int = 5) -> list[dict]:
    """
    Main entry point — called by fetcher agent.
    Runs parallel fetch synchronously.
    """
    return asyncio.run(fetch_all_sources_parallel(query, location, num_jobs))