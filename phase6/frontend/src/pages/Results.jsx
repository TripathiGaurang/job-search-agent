import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Clock, Zap } from "lucide-react";
import JobCard from "../components/JobCard";
import { updateJobStatus } from "../services/api";

export default function Results() {
  const navigate = useNavigate();
  const [results, setResults] = useState(null);

  useEffect(() => {
    const stored = sessionStorage.getItem("searchResults");
    if (!stored) { navigate("/"); return; }
    setResults(JSON.parse(stored));
  }, []);

  const handleStatusUpdate = async (jobId, status) => {
    await updateJobStatus(jobId, status);
    setResults(prev => ({
      ...prev,
      jobs: prev.jobs.map(j =>
        j.job_id === jobId ? {...j, status} : j
      )
    }));
  };

  if (!results) return null;

  return (
    <div style={{ maxWidth: "800px", margin: "0 auto", padding: "24px" }}>

      {/* Back button */}
      <button
        onClick={() => navigate("/")}
        style={{
          display: "flex", alignItems: "center", gap: "6px",
          background: "none", border: "none",
          color: "var(--gray-600)", cursor: "pointer",
          fontSize: "14px", marginBottom: "20px", padding: 0
        }}
      >
        <ArrowLeft size={16} /> New Search
      </button>

      {/* Stats bar */}
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(4, 1fr)",
        gap: "12px", marginBottom: "24px"
      }}>
        {[
          { label: "Total Found",   value: results.total_found },
          { label: "New Jobs",      value: results.new_jobs },
          { label: "Already Seen",  value: results.skipped },
          { label: "Score Time",    value: `${results.score_time}s ⚡` },
        ].map(stat => (
          <div key={stat.label} style={{
            background: "white",
            border: "1px solid var(--gray-200)",
            borderRadius: "10px",
            padding: "16px",
            textAlign: "center"
          }}>
            <div style={{ fontSize: "22px", fontWeight: 700, color: "var(--primary)" }}>
              {stat.value}
            </div>
            <div style={{ fontSize: "12px", color: "var(--gray-600)", marginTop: "2px" }}>
              {stat.label}
            </div>
          </div>
        ))}
      </div>

      {/* Results header */}
      <h2 style={{ fontSize: "20px", fontWeight: 700, marginBottom: "16px" }}>
        🏆 Ranked Job Matches
        <span style={{ fontSize: "14px", fontWeight: 400, color: "var(--gray-600)", marginLeft: "8px" }}>
          ({results.jobs?.length || 0} results)
        </span>
      </h2>

      {/* Error list */}
      {results.errors?.length > 0 && (
        <div style={{
          background: "#fff7ed", border: "1px solid #fed7aa",
          borderRadius: "8px", padding: "12px", marginBottom: "16px",
          fontSize: "13px", color: "#c2410c"
        }}>
          ⚠️ Some sources had issues: {results.errors.join(", ")}
        </div>
      )}

      {/* Job cards */}
      {results.jobs?.length === 0 ? (
        <div style={{
          textAlign: "center", padding: "60px",
          color: "var(--gray-400)"
        }}>
          <div style={{ fontSize: "48px", marginBottom: "16px" }}>🔍</div>
          <p>No new jobs found this run. Try a different query or check back later.</p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {results.jobs.map((job, i) => (
            <JobCard
              key={job.job_id || i}
              job={job}
              onStatusUpdate={handleStatusUpdate}
              showActions={true}
            />
          ))}
        </div>
      )}
    </div>
  );
}