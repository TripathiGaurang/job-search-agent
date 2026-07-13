import { Link, useLocation } from "react-router-dom";
import { Search, BookMarked, Home } from "lucide-react";

export default function Navbar() {
  const location = useLocation();

  const links = [
    { to: "/",        label: "Search",  icon: <Search size={16} /> },
    { to: "/history", label: "History", icon: <BookMarked size={16} /> },
  ];

  return (
    <nav style={{
      background: "white",
      borderBottom: "1px solid var(--gray-200)",
      padding: "0 24px",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      height: "60px",
      position: "sticky",
      top: 0,
      zIndex: 100,
      boxShadow: "0 1px 3px rgba(0,0,0,0.05)"
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <span style={{ fontSize: "20px" }}>🤖</span>
        <span style={{ fontWeight: 700, fontSize: "16px", color: "var(--gray-800)" }}>
          Job Search Agent
        </span>
      </div>

      <div style={{ display: "flex", gap: "8px" }}>
        {links.map(link => (
          <Link
            key={link.to}
            to={link.to}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "8px 16px",
              borderRadius: "8px",
              textDecoration: "none",
              fontSize: "14px",
              fontWeight: 500,
              background: location.pathname === link.to ? "var(--primary)" : "transparent",
              color: location.pathname === link.to ? "white" : "var(--gray-600)",
              transition: "all 0.2s"
            }}
          >
            {link.icon} {link.label}
          </Link>
        ))}
      </div>
    </nav>
  );
}