import { useState, useEffect }    from "react";
import { Search, Layers, Filter } from "lucide-react";
import JobCard                    from "../components/JobCard";
import {
    getSavedJobs,
    updateJobStatus,
    findSimilarJobs,
    findJobsSimilarTo
} from "../services/api";

export default function History() {
    const [jobs,          setJobs]          = useState([]);
    const [loading,       setLoading]       = useState(false);
    const [email,         setEmail]         = useState("");
    const [filter,        setFilter]        = useState("all");
    const [minScore,      setMinScore]      = useState(0);
    const [searched,      setSearched]      = useState(false);
    const [similarQuery,  setSimilarQuery]  = useState("");
    const [similarResults,setSimilarResults]= useState([]);
    const [similarLoading,setSimilarLoading]= useState(false);
    const [activeTab,     setActiveTab]     = useState("history");
    const [similarLabel,  setSimilarLabel]  = useState("");

    useEffect(() => {
        const stored = sessionStorage.getItem("userEmail");
        if (stored) {
            setEmail(stored);
            fetchHistory(stored);
        }
    }, []);

    const fetchHistory = async (emailToUse) => {
        if (!emailToUse) return;
        setLoading(true);
        try {
            const data = await getSavedJobs(emailToUse, minScore);
            setJobs(data.jobs || []);
            setSearched(true);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleStatusUpdate = async (jobId, status) => {
        await updateJobStatus(jobId, status);
        setJobs(prev => prev.map(j =>
            j.job_id === jobId ? { ...j, status } : j
        ));
        setSimilarResults(prev => prev.map(j =>
            j.job_id === jobId ? { ...j, status } : j
        ));
    };

    // Called when user types query and clicks Search
    const handleSimilarSearch = async () => {
        if (!similarQuery.trim()) return;
        setSimilarLoading(true);
        setSimilarResults([]);
        setSimilarLabel(`Results for "${similarQuery}"`);
        try {
            const data = await findSimilarJobs(email, similarQuery);
            setSimilarResults(data.jobs || []);
            setActiveTab("similar");
        } catch (err) {
            console.error(err);
        } finally {
            setSimilarLoading(false);
        }
    };

    // Called when user clicks "Find Similar" on a job card
    const handleFindSimilar = async (jobId) => {
        setSimilarLoading(true);
        setSimilarResults([]);
        setActiveTab("similar");
        const sourceJob = jobs.find(j => j.job_id === jobId);
        setSimilarLabel(`Similar to "${sourceJob?.title}"`);
        try {
            const data = await findJobsSimilarTo(email, jobId);
            setSimilarResults(data.similar || []);
            window.scrollTo({ top: 0, behavior: "smooth" });
        } catch (err) {
            console.error(err);
        } finally {
            setSimilarLoading(false);
        }
    };

    const filtered = jobs.filter(j => {
        if (filter === "all")      return true;
        if (filter === "applied")  return j.status === "applied";
        if (filter === "rejected") return j.status === "rejected";
        if (filter === "unseen")   return j.status === "seen";
        return true;
    });

    return (
        <div style={{ maxWidth: "800px", margin: "0 auto", padding: "24px" }}>
            <h2 style={{ fontSize: "22px", fontWeight: 700, marginBottom: "20px" }}>
                📂 Job History
            </h2>

            {/* Email + Score filter */}
            <div style={{
                background: "white", border: "1px solid var(--gray-200)",
                borderRadius: "12px", padding: "20px", marginBottom: "20px",
                display: "flex", gap: "12px", alignItems: "flex-end"
            }}>
                <div style={{ flex: 1 }}>
                    <label style={{
                        fontSize: "13px", fontWeight: 600,
                        color: "var(--gray-600)", display: "block", marginBottom: "6px"
                    }}>
                        Your Email
                    </label>
                    <input
                        type        = "email"
                        value       = {email}
                        onChange    = {e => setEmail(e.target.value)}
                        placeholder = "you@gmail.com"
                        style={{
                            width: "100%", padding: "10px 14px",
                            border: "1px solid var(--gray-200)",
                            borderRadius: "8px", fontSize: "14px", outline: "none"
                        }}
                    />
                </div>
                <div>
                    <label style={{
                        fontSize: "13px", fontWeight: 600,
                        color: "var(--gray-600)", display: "block", marginBottom: "6px"
                    }}>
                        Min Score: {minScore}
                    </label>
                    <input
                        type     = "range"
                        min      = "0"
                        max      = "10"
                        value    = {minScore}
                        onChange = {e => setMinScore(parseInt(e.target.value))}
                        style    = {{ width: "120px" }}
                    />
                </div>
                <button
                    onClick  = {() => fetchHistory(email)}
                    disabled = {loading}
                    style={{
                        background: "var(--primary)", color: "white",
                        padding: "10px 20px", borderRadius: "8px",
                        border: "none", cursor: "pointer",
                        fontWeight: 600, fontSize: "14px"
                    }}
                >
                    {loading ? "Loading..." : "Load"}
                </button>
            </div>

            {/* Semantic Search Box */}
            {searched && (
                <div style={{
                    background: "white", border: "1px solid var(--gray-200)",
                    borderRadius: "12px", padding: "20px", marginBottom: "20px"
                }}>
                    <h3 style={{
                        fontSize: "15px", fontWeight: 600,
                        marginBottom: "4px", color: "var(--gray-800)"
                    }}>
                        🔍 Semantic Job Search
                    </h3>
                    <p style={{
                        fontSize: "13px", color: "var(--gray-600)", marginBottom: "12px"
                    }}>
                        Search by meaning — finds similar jobs even without exact keyword matches.
                    </p>
                    <div style={{ display: "flex", gap: "10px" }}>
                        <input
                            type        = "text"
                            value       = {similarQuery}
                            onChange    = {e => setSimilarQuery(e.target.value)}
                            onKeyDown   = {e => e.key === "Enter" && handleSimilarSearch()}
                            placeholder = "e.g. React SharePoint developer, Power Platform architect..."
                            style={{
                                flex: 1, padding: "10px 14px",
                                border: "1px solid var(--gray-200)",
                                borderRadius: "8px", fontSize: "14px", outline: "none"
                            }}
                        />
                        <button
                            onClick  = {handleSimilarSearch}
                            disabled = {similarLoading || !similarQuery.trim()}
                            style={{
                                display: "flex", alignItems: "center", gap: "6px",
                                background: similarLoading ? "var(--gray-400)" : "var(--primary)",
                                color: "white", padding: "10px 20px",
                                borderRadius: "8px", border: "none",
                                cursor: similarLoading ? "not-allowed" : "pointer",
                                fontSize: "14px", fontWeight: 600
                            }}
                        >
                            <Search size={16} />
                            {similarLoading ? "Searching..." : "Search"}
                        </button>
                    </div>
                </div>
            )}

            {/* Tab switcher */}
            {searched && (
                <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
                    {[
                        { id: "history", label: `All Jobs (${jobs.length})` },
                        { id: "similar", label: similarResults.length > 0
                            ? `${similarLabel} (${similarResults.length})`
                            : "Similar Search"
                        }
                    ].map(tab => (
                        <button
                            key     = {tab.id}
                            onClick = {() => setActiveTab(tab.id)}
                            style={{
                                padding: "6px 16px", borderRadius: "20px",
                                border: "1px solid var(--gray-200)",
                                background: activeTab === tab.id ? "var(--primary)" : "white",
                                color: activeTab === tab.id ? "white" : "var(--gray-600)",
                                cursor: "pointer", fontSize: "13px",
                                fontWeight: activeTab === tab.id ? 600 : 400
                            }}
                        >
                            {tab.label}
                        </button>
                    ))}

                    {/* Status filter — only show on history tab */}
                    {activeTab === "history" && (
                        <>
                            {["all", "unseen", "applied", "rejected"].map(f => (
                                <button
                                    key     = {f}
                                    onClick = {() => setFilter(f)}
                                    style={{
                                        padding: "6px 16px", borderRadius: "20px",
                                        border: "1px solid var(--gray-200)",
                                        background: filter === f ? "var(--gray-800)" : "white",
                                        color: filter === f ? "white" : "var(--gray-600)",
                                        cursor: "pointer", fontSize: "13px",
                                        textTransform: "capitalize"
                                    }}
                                >
                                    {f}
                                </button>
                            ))}
                        </>
                    )}
                </div>
            )}

            {/* Job Cards */}
            {loading ? (
                <div style={{ textAlign: "center", padding: "60px", color: "var(--gray-400)" }}>
                    Loading your job history...
                </div>
            ) : activeTab === "similar" ? (
                similarLoading ? (
                    <div style={{ textAlign: "center", padding: "60px", color: "var(--gray-400)" }}>
                        🔍 Searching semantically...
                    </div>
                ) : similarResults.length === 0 ? (
                    <div style={{ textAlign: "center", padding: "60px", color: "var(--gray-400)" }}>
                        <div style={{ fontSize: "48px", marginBottom: "12px" }}>🔍</div>
                        <p>No similar jobs found. Try a different query or run a search first to build your history.</p>
                    </div>
                ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                        {similarResults.map((job, i) => (
                            <div key={job.job_id || i}>
                                {/* Similarity badge */}
                                <div style={{
                                    display: "inline-block",
                                    background: job.similarity >= 70 ? "#f0fdf4" : "#eff6ff",
                                    color: job.similarity >= 70 ? "#22c55e" : "#2563eb",
                                    padding: "3px 10px", borderRadius: "4px",
                                    fontSize: "12px", fontWeight: 600, marginBottom: "6px"
                                }}>
                                    {job.similarity}% match
                                </div>
                                <JobCard
                                    job            = {job}
                                    onStatusUpdate = {handleStatusUpdate}
                                    onFindSimilar  = {handleFindSimilar}
                                    showActions    = {true}
                                />
                            </div>
                        ))}
                    </div>
                )
            ) : (
                filtered.length === 0 && searched ? (
                    <div style={{ textAlign: "center", padding: "60px", color: "var(--gray-400)" }}>
                        <div style={{ fontSize: "48px", marginBottom: "12px" }}>📭</div>
                        <p>No jobs found for this filter.</p>
                    </div>
                ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                        {filtered.map((job, i) => (
                            <JobCard
                                key            = {job.job_id || i}
                                job            = {job}
                                onStatusUpdate = {handleStatusUpdate}
                                onFindSimilar  = {handleFindSimilar}
                                showActions    = {true}
                            />
                        ))}
                    </div>
                )
            )}
        </div>
    );
}