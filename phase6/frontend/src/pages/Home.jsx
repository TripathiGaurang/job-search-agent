import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, Search, Loader } from "lucide-react";
import { searchJobs } from "../services/api";

export default function Home() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email    : "",
    query    : "SharePoint Developer",
    location : "Gurugram",
    num_jobs : 5,
  });
  const [resume,   setResume]   = useState(null);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState("");

  const handleSubmit = async () => {
    if (!resume)       return setError("Please upload your resume.");
    if (!form.email)   return setError("Please enter your email.");
    if (!form.query)   return setError("Please enter a job title.");
    if (!form.location)return setError("Please enter a location.");

    setLoading(true);
    setError("");

    try {
      const data = new FormData();
      data.append("email",    form.email);
      data.append("query",    form.query);
      data.append("location", form.location);
      data.append("num_jobs", form.num_jobs);
      data.append("resume",   resume);

      const results = await searchJobs(data);

      // Store results and navigate to results page
      sessionStorage.setItem("searchResults", JSON.stringify(results));
      sessionStorage.setItem("userEmail",     form.email);
      navigate("/results");

    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong. Check your backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "var(--gray-50)" }}>

      {/* Hero */}
      <div style={{
        background: "linear-gradient(135deg, #1e293b 0%, #2563eb 100%)",
        color: "white",
        padding: "60px 24px",
        textAlign: "center"
      }}>
        <div style={{ fontSize: "48px", marginBottom: "16px" }}>🤖</div>
        <h1 style={{ fontSize: "36px", fontWeight: 700, marginBottom: "12px" }}>
          Job Search Agent
        </h1>
        <p style={{ fontSize: "18px", opacity: 0.8, maxWidth: "500px", margin: "0 auto" }}>
          Upload your resume. We'll find and rank the best matching jobs for you using AI.
        </p>
      </div>

      {/* Form */}
      <div style={{
        maxWidth: "600px",
        margin: "-40px auto 0",
        padding: "0 24px 60px"
      }}>
        <div style={{
          background: "white",
          borderRadius: "16px",
          padding: "32px",
          boxShadow: "0 4px 24px rgba(0,0,0,0.08)"
        }}>

          {/* Email */}
          <div style={{ marginBottom: "20px" }}>
            <label style={{ display: "block", fontSize: "13px", fontWeight: 600, marginBottom: "6px", color: "var(--gray-600)" }}>
              Your Email (results will be sent here)
            </label>
            <input
              type="email"
              placeholder="you@gmail.com"
              value={form.email}
              onChange={e => setForm({...form, email: e.target.value})}
              style={{
                width: "100%", padding: "10px 14px",
                border: "1px solid var(--gray-200)",
                borderRadius: "8px", fontSize: "14px",
                outline: "none"
              }}
            />
          </div>

          {/* Resume Upload */}
          <div style={{ marginBottom: "20px" }}>
            <label style={{ display: "block", fontSize: "13px", fontWeight: 600, marginBottom: "6px", color: "var(--gray-600)" }}>
              Resume (PDF)
            </label>
            <div
              onClick={() => document.getElementById("resume-input").click()}
              style={{
                border: `2px dashed ${resume ? "#22c55e" : "var(--gray-200)"}`,
                borderRadius: "8px",
                padding: "24px",
                textAlign: "center",
                cursor: "pointer",
                background: resume ? "#f0fdf4" : "var(--gray-50)",
                transition: "all 0.2s"
              }}
            >
              <Upload size={24} style={{ color: resume ? "#22c55e" : "var(--gray-400)", margin: "0 auto 8px" }} />
              <p style={{ fontSize: "14px", color: resume ? "#22c55e" : "var(--gray-600)", fontWeight: 500 }}>
                {resume ? `✓ ${resume.name}` : "Click to upload your resume PDF"}
              </p>
              <p style={{ fontSize: "12px", color: "var(--gray-400)", marginTop: "4px" }}>
                PDF only
              </p>
              <input
                id="resume-input"
                type="file"
                accept=".pdf"
                style={{ display: "none" }}
                onChange={e => setResume(e.target.files[0])}
              />
            </div>
          </div>

          {/* Job Title */}
          <div style={{ marginBottom: "20px" }}>
            <label style={{ display: "block", fontSize: "13px", fontWeight: 600, marginBottom: "6px", color: "var(--gray-600)" }}>
              Job Title / Role
            </label>
            <input
              type="text"
              placeholder="e.g. SharePoint Developer"
              value={form.query}
              onChange={e => setForm({...form, query: e.target.value})}
              style={{
                width: "100%", padding: "10px 14px",
                border: "1px solid var(--gray-200)",
                borderRadius: "8px", fontSize: "14px", outline: "none"
              }}
            />
          </div>

          {/* Location */}
          <div style={{ marginBottom: "20px" }}>
            <label style={{ display: "block", fontSize: "13px", fontWeight: 600, marginBottom: "6px", color: "var(--gray-600)" }}>
              Location
            </label>
            <input
              type="text"
              placeholder="e.g. Gurugram"
              value={form.location}
              onChange={e => setForm({...form, location: e.target.value})}
              style={{
                width: "100%", padding: "10px 14px",
                border: "1px solid var(--gray-200)",
                borderRadius: "8px", fontSize: "14px", outline: "none"
              }}
            />
          </div>

          {/* Number of jobs */}
          <div style={{ marginBottom: "24px" }}>
            <label style={{ display: "block", fontSize: "13px", fontWeight: 600, marginBottom: "6px", color: "var(--gray-600)" }}>
              Jobs per source: {form.num_jobs}
            </label>
            <input
              type="range" min="3" max="10"
              value={form.num_jobs}
              onChange={e => setForm({...form, num_jobs: parseInt(e.target.value)})}
              style={{ width: "100%" }}
            />
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "var(--gray-400)" }}>
              <span>3</span><span>10</span>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div style={{
              background: "#fef2f2", border: "1px solid #fecaca",
              borderRadius: "8px", padding: "12px", marginBottom: "16px",
              color: "#ef4444", fontSize: "14px"
            }}>
              ⚠️ {error}
            </div>
          )}

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={loading}
            style={{
              width: "100%",
              display: "flex", alignItems: "center", justifyContent: "center", gap: "8px",
              background: loading ? "var(--gray-400)" : "var(--primary)",
              color: "white",
              padding: "14px",
              borderRadius: "10px",
              border: "none",
              fontSize: "16px",
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
              transition: "background 0.2s"
            }}
          >
            {loading ? (
              <><Loader size={18} className="spin" /> Searching... (this takes ~30 seconds)</>
            ) : (
              <><Search size={18} /> Find My Jobs</>
            )}
          </button>

          {loading && (
            <p style={{ textAlign: "center", fontSize: "13px", color: "var(--gray-400)", marginTop: "12px" }}>
              🤖 Agent is fetching from 4 sources, scoring with AI, and ranking results...
            </p>
          )}
        </div>
      </div>
    </div>
  );
}