import os
import requests
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

def fetch_jobs(query: str, location: str, num_jobs: int = 5) -> list[dict]:
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
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        if response.status_code != 200:
            print(f"❌ API Error: {data}")
            return []

        # response structure: data -> data -> jobs -> [list of jobs]
        jobs_list = data.get("data", {}).get("jobs", [])

        jobs = []
        for job in jobs_list[:num_jobs]:
            jobs.append({
                "job_id"  : job.get("job_id", "N/A"),   # ← NEW fingerprint
                "title"   : job.get("job_title", "N/A"),
                "company" : job.get("employer_name", "N/A"),
                "location": job.get("job_city", location),
                "summary" : job.get("job_description", "N/A")[:600],
                "link"    : job.get("job_apply_link", "N/A"),
                "source"  : job.get("job_publisher", "N/A")
            })

        return jobs

    except Exception as e:
        print(f"❌ Exception: {e}")
        return []


if __name__ == "__main__":
    print("🔍 Fetching jobs...\n")
    jobs = fetch_jobs("SharePoint Developer", "Gurugram")

    if not jobs:
        print("No jobs found.")
    else:
        for i, job in enumerate(jobs, 1):
            print(f"--- Job {i} ---")
            print(f"Title   : {job['title']}")
            print(f"Company : {job['company']}")
            print(f"Source  : {job['source']}")
            print(f"Link    : {job['link']}")
            print()