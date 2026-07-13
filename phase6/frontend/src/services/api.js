import axios from "axios";

const BASE_URL = "http://127.0.0.1:8000";

const api = axios.create({ baseURL: BASE_URL });

// Search jobs — sends resume + form data
export const searchJobs = async (formData) => {
  const response = await api.post("/search", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};

// Get saved jobs for a user
export const getSavedJobs = async (email, minScore = 0) => {
  const response = await api.get(`/jobs/${email}?min_score=${minScore}`);
  return response.data;
};

// Update job status
export const updateJobStatus = async (jobId, status) => {
  const response = await api.put(`/jobs/${jobId}/status`, { status });
  return response.data;
};

// Search saved jobs by text query
export const findSimilarJobs = async (email, query, topK = 5) => {
    const response = await api.get(
        `/jobs/${email}/similar?query=${encodeURIComponent(query)}&top_k=${topK}`
    );
    return response.data;
};

// Find jobs similar to a specific saved job
export const findJobsSimilarTo = async (email, jobId, topK = 5) => {
    const response = await api.get(
        `/jobs/${email}/similar-to/${jobId}?top_k=${topK}`
    );
    return response.data;
};