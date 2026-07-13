import { ExternalLink, CheckCircle, XCircle, Search } from "lucide-react";

const VERDICT_CONFIG = {
  STRONG_MATCH: { color: "#22c55e", bg: "#f0fdf4", emoji: "🟢" },
  GOOD_MATCH:   { color: "#eab308", bg: "#fefce8", emoji: "🟡" },
  WEAK_MATCH:   { color: "#f97316", bg: "#fff7ed", emoji: "🟠" },
  NO_MATCH:     { color: "#ef4444", bg: "#fef2f2", emoji: "🔴" },
};

export default function JobCard({ job, onStatusUpdate, onFindSimilar, showActions = true }) {
  const config  = VERDICT_CONFIG[job.verdict] || { color: "#6b7280", bg: "#f9fafb", emoji: "⚪" };
  const missing = job.missing_skills?.join(", ") || "None";
  const matching = job.matching_skills?.join(", ") || "N/A";

  return (
    <div style={{
      background: "white",
      border: "1px solid var(--gray-200)",
      borderRadius: "12px",
      padding: "20px",
      transition: "box-shadow 0.2s",
    }}
    onMouseEnter={e => e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.08)"}
    onMouseLeave={e => e.currentTarget.style.boxShadow = "none"}
    >
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
        <div style={{ flex: 1 }}>
          <h3 style={{ fontSize: "16px", fontWeight: 600, marginBottom: "4px" }}>
            {job.title}
          </h3>
          <p style={{ color: "var(--gray-600)", fontSize: "14px" }}>
            {job.company} · {job.location}
          </p>
        </div>
        <div style={{
          background: config.bg,
          color: config.color,
          padding: "4px 12px",
          borderRadius: "20px",
          fontSize: "13px",
          fontWeight: 600,
          whiteSpace: "nowrap",
          marginLeft: "12px"
        }}>
          {config.emoji} {job.score}/10
        </div>
      </div>

      {/* Source badge */}
      <div style={{ marginBottom: "12px" }}>
        <span style={{
          background: "var(--gray-100)",
          color: "var(--gray-600)",
          padding: "2px 8px",
          borderRadius: "4px",
          fontSize: "12px"
        }}>
          {job.source}
        </span>
        {job.status && job.status !== "seen" && (
          <span style={{
            background: job.status === "applied" ? "#eff6ff" : "#fef2f2",
            color: job.status === "applied" ? "#2563eb" : "#ef4444",
            padding: "2px 8px",
            borderRadius: "4px",
            fontSize: "12px",
            marginLeft: "6px",
            fontWeight: 500
          }}>
            {job.status === "applied" ? "✓ Applied" : "✕ Rejected"}
          </span>
        )}
      </div>

      {/* Skills */}
      <div style={{ marginBottom: "12px", fontSize: "13px" }}>
        <div style={{ marginBottom: "4px" }}>
          <span style={{ color: "var(--gray-600)" }}>✅ Matching: </span>
          <span>{matching}</span>
        </div>
        <div>
          <span style={{ color: "var(--gray-600)" }}>❌ Missing: </span>
          <span style={{ color: missing === "None" ? "#22c55e" : "inherit" }}>{missing}</span>
        </div>
      </div>

      {/* Reason */}
      <p style={{
        fontSize: "13px",
        color: "var(--gray-600)",
        lineHeight: "1.5",
        marginBottom: "16px",
        padding: "10px",
        background: "var(--gray-50)",
        borderRadius: "6px"
      }}>
        {job.reason}
      </p>

      {/* Actions */}
      <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
        {onFindSimilar && (
          <button
            onClick={() => onFindSimilar(job.job_id)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "4px",
              background: "#eff6ff",
              color: "#2563eb",
              border: "1px solid #bfdbfe",
              padding: "8px 16px",
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: "13px",
              fontWeight: 500
            }}
          >
            <Search size={14} /> Find Similar
          </button>
        )}

        <a
          href={job.link}
          target="_blank"
          rel="noreferrer"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "4px",
            background: "var(--primary)",
            color: "white",
            padding: "8px 16px",
            borderRadius: "8px",
            textDecoration: "none",
            fontSize: "13px",
            fontWeight: 500
          }}
        >
          Apply Now <ExternalLink size={14} />
        </a>

        {showActions && onStatusUpdate && (
          <>
            <button
              onClick={() => onStatusUpdate(job.job_id, "applied")}
              style={{
                display: "flex", alignItems: "center", gap: "4px",
                background: "#eff6ff", color: "#2563eb",
                border: "1px solid #bfdbfe",
                padding: "8px 16px", borderRadius: "8px",
                cursor: "pointer", fontSize: "13px"
              }}
            >
              <CheckCircle size={14} /> Applied
            </button>
            <button
              onClick={() => onStatusUpdate(job.job_id, "rejected")}
              style={{
                display: "flex", alignItems: "center", gap: "4px",
                background: "#fef2f2", color: "#ef4444",
                border: "1px solid #fecaca",
                padding: "8px 16px", borderRadius: "8px",
                cursor: "pointer", fontSize: "13px"
              }}
            >
              <XCircle size={14} /> Reject
            </button>
          </>
        )}
      </div>
    </div>
  );
}