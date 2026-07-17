import os
import requests
from dotenv import load_dotenv

load_dotenv()

ADZUNA_APP_ID  = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

# Maps user-entered city names to Adzuna's exact location hierarchy
# Adzuna India uses: location0=India, location1=State, location2=City
LOCATION_MAP = {
    # NCR
    "gurugram"   : ("Haryana",           "Gurgaon"),
    "gurgaon"    : ("Haryana",           "Gurgaon"),
    "noida"      : ("Uttar Pradesh",     "Noida"),
    "delhi"      : ("Delhi",             "Delhi"),
    "new delhi"  : ("Delhi",             "Delhi"),
    "faridabad"  : ("Haryana",           "Faridabad"),
    "ghaziabad"  : ("Uttar Pradesh",     "Ghaziabad"),

    # South India
    "bangalore"  : ("Karnataka",         "Bangalore"),
    "bengaluru"  : ("Karnataka",         "Bangalore"),
    "bengaluru"  : ("Karnataka",         "Bangalore"),
    "hyderabad"  : ("Telangana",         "Hyderabad"),
    "chennai"    : ("Tamil Nadu",        "Chennai"),
    "coimbatore" : ("Tamil Nadu",        "Coimbatore"),
    "kochi"      : ("Kerala",            "Kochi"),
    "trivandrum" : ("Kerala",            "Trivandrum"),

    # West India
    "mumbai"     : ("Maharashtra",       "Mumbai"),
    "pune"       : ("Maharashtra",       "Pune"),
    "ahmedabad"  : ("Gujarat",           "Ahmedabad"),
    "surat"      : ("Gujarat",           "Surat"),

    # North India
    "chandigarh" : ("Punjab",            "Chandigarh"),
    "lucknow"    : ("Uttar Pradesh",     "Lucknow"),
    "jaipur"     : ("Rajasthan",         "Jaipur"),
    "indore"     : ("Madhya Pradesh",    "Indore"),

    # East India
    "kolkata"    : ("West Bengal",       "Kolkata"),
    "bhubaneswar": ("Orissa",            "Bhubaneswar"),

    # Special — search all India
    "india"      : None,
    "remote"     : None,
    "pan india"  : None,
}


def _build_params(query: str, location_key: str, num_jobs: int) -> dict:
    """
    Builds the correct Adzuna API params based on location.
    Handles three cases:
      1. Known city    → use location0 + location1 + location2
      2. All India     → use location0 only
      3. Unknown city  → use location0 only (safe fallback)
    """
    base = {
        "app_id"          : ADZUNA_APP_ID,
        "app_key"         : ADZUNA_APP_KEY,
        "results_per_page": num_jobs,
        "what"            : query,
        "sort_by"         : "date"
    }

    # Check if location is in our map
    mapped = LOCATION_MAP.get(location_key)

    if location_key in LOCATION_MAP and mapped is not None:
        # Known city — use full location hierarchy
        state, city = mapped
        base["location0"] = "India"
        base["location1"] = state
        base["location2"] = city
        print(f"   Location mapped: {city}, {state}")

    elif location_key in LOCATION_MAP and mapped is None:
        # Explicitly set to all India (remote/pan india/india)
        base["location0"] = "India"
        print(f"   Searching all India...")

    else:
        # Unknown city — fall back to all India
        base["location0"] = "India"
        print(f"   '{location_key}' not in location map — searching all India")

    return base


def _call_adzuna(params: dict) -> list:
    """
    Makes a single API call to Adzuna.
    Returns list of raw job results or empty list on failure.
    """
    try:
        response = requests.get(
            "https://api.adzuna.com/v1/api/jobs/in/search/1",
            params  = params,
            timeout = 15
        )

        if response.status_code != 200:
            print(f"   Adzuna API error {response.status_code}: {response.text[:150]}")
            return []

        return response.json().get("results", [])

    except requests.Timeout:
        print("   Adzuna timed out after 15s")
        return []
    except Exception as e:
        print(f"   Adzuna error: {e}")
        return []


def _parse_jobs(results: list, location: str) -> list:
    """
    Converts raw Adzuna results into our standard job dict format.
    Same structure used throughout the agent pipeline.
    """
    jobs = []
    for job in results:
        jobs.append({
            "job_id"  : str(job.get("id", "")),
            "title"   : job.get("title", "N/A"),
            "company" : job.get("company", {}).get("display_name", "N/A"),
            "location": job.get("location", {}).get("display_name", location),
            "summary" : job.get("description", "")[:600],
            "link"    : job.get("redirect_url", "N/A"),
            "source"  : "Adzuna"
        })
    return jobs


def fetch_from_adzuna(query: str, location: str, num_jobs: int = 5) -> list:
    """
    Fetches jobs from Adzuna with smart location handling.

    Strategy:
      1. Search specific city if location is known
      2. If fewer than num_jobs results — expand to all India
      3. Parse and return standardised job dicts
    """
    print(f"   Fetching from Adzuna: {query} in {location}...")

    location_key = location.lower().strip()

    # Build params for specific city search
    params = _build_params(query, location_key, num_jobs)

    # Step 1 — Try specific location
    results = _call_adzuna(params)
    print(f"   City search: {len(results)} results")

    # Step 2 — Expand to all India if not enough results
    # Only expand if we were searching a specific city
    # (don't expand if we were already searching all India)
    if len(results) < num_jobs and "location2" in params:
        print(f"   Fewer than {num_jobs} results — expanding to all India...")
        india_params = {
            "app_id"          : ADZUNA_APP_ID,
            "app_key"         : ADZUNA_APP_KEY,
            "results_per_page": num_jobs,
            "what"            : query,
            "location0"       : "India",
            "sort_by"         : "date"
        }
        india_results = _call_adzuna(india_params)
        print(f"   India-wide search: {len(india_results)} results")

        # Merge — city results first (more relevant), then India-wide
        existing_ids = {str(r.get("id", "")) for r in results}
        for r in india_results:
            if str(r.get("id", "")) not in existing_ids:
                results.append(r)

    jobs = _parse_jobs(results[:num_jobs], location)
    print(f"   Adzuna: {len(jobs)} jobs returned")
    return jobs


def fetch_jobs(query: str, location: str, num_jobs: int = 5) -> list:
    """
    Main entry point called by the fetcher agent.
    Fetches, deduplicates, and returns jobs.
    """
    all_jobs = fetch_from_adzuna(query, location, num_jobs)

    # Deduplicate by job_id
    seen_ids    = set()
    unique_jobs = []
    for job in all_jobs:
        if job["job_id"] and job["job_id"] not in seen_ids:
            seen_ids.add(job["job_id"])
            unique_jobs.append(job)

    print(f"   Total unique jobs: {len(unique_jobs)}")
    return unique_jobs


if __name__ == "__main__":
    # Quick test — run directly to verify
    print("Testing Gurugram:")
    jobs = fetch_jobs("SharePoint Developer", "Gurugram", 5)
    for j in jobs:
        print(f"  {j['title']} - {j['company']} - {j['location']}")

    print("\nTesting Bengaluru:")
    jobs = fetch_jobs("SharePoint Developer", "Bengaluru", 5)
    for j in jobs:
        print(f"  {j['title']} - {j['company']} - {j['location']}")

    print("\nTesting Unknown City:")
    jobs = fetch_jobs("SharePoint Developer", "Jaipur", 5)
    for j in jobs:
        print(f"  {j['title']} - {j['company']} - {j['location']}")