import Link from "next/link";

const colors = {
  navy: "var(--navy)",
  navy2: "var(--navy2)",
  navy3: "var(--navy3)",
  saffron: "var(--saffron)",
  green: "var(--green)",
  red: "var(--red)",
  muted: "var(--muted)",
  border: "var(--border)"
};

export const shellStyle = {
  width: "min(1180px, calc(100% - 32px))",
  margin: "0 auto",
  padding: "24px 0"
};

export const gridStyle = {
  display: "grid",
  gap: 16
};

export function Navbar() {
  return (
    <nav>
      <Link href="/" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none" }}>
        <span style={{ display: "grid", placeItems: "center", width: 34, height: 34, borderRadius: 6, background: colors.saffron, color: colors.navy2, fontWeight: 700 }}>N</span>
        <span>
          <span className="nav-logo">NyayaSetu AI</span>
          <span style={{ display: "block", color: colors.muted, fontSize: 11 }}>Justice Starts Here</span>
        </span>
      </Link>
      <div className="nav-links">
        <Link href="/">Dashboard</Link>
        <Link href="/demo">Demo</Link>
        <Link href="/zamanat">ZamanatAI</Link>
        <Link href="/civicdocs">CivicDocs</Link>
        <Link href="/dataset">Dataset</Link>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span className="badge badge-green"><span className="live-dot" />Live</span>
        <select aria-label="Language selector" style={{ width: 118, padding: "7px 10px" }}>
          <option>English</option>
          <option>हिन्दी</option>
          <option>मराठी</option>
          <option>தமிழ்</option>
        </select>
      </div>
    </nav>
  );
}

export function PageHero({ kicker, title, children }) {
  return (
    <section className="card2" style={{ animation: "slide-up .35s ease" }}>
      <p className="section-title" style={{ color: colors.saffron }}>{kicker}</p>
      <h1 style={{ maxWidth: 820, fontSize: "clamp(30px, 6vw, 58px)", lineHeight: 1.02, letterSpacing: "-.04em", fontWeight: 600 }}>{title}</h1>
      {children && <div style={{ marginTop: 16, maxWidth: 720, color: "rgba(255,255,255,.68)" }}>{children}</div>}
    </section>
  );
}

export function ScoreRing({ score = 82, label = "Justice Readiness" }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
      <div style={{ width: 96, height: 96, borderRadius: "50%", background: `conic-gradient(${colors.saffron} ${score}%, rgba(255,255,255,.08) 0)`, display: "grid", placeItems: "center", flex: "0 0 auto" }}>
        <div style={{ width: 66, height: 66, borderRadius: "50%", background: colors.navy2, display: "grid", placeItems: "center", color: "#fff", fontFamily: "var(--mono)", fontSize: 20 }}>{score}%</div>
      </div>
      <div>
        <div className="section-title" style={{ marginBottom: 2, color: colors.saffron }}>{label}</div>
        <p style={{ color: colors.muted }}>Evidence, documents, timeline, and legal route converted into one action score.</p>
      </div>
    </div>
  );
}

export function JourneyEngine({ compact = false }) {
  const stages = ["Issue Detected", "Evidence Collected", "Documents Generated", "Legal Route", "Legal Aid", "Court Ready"];
  return (
    <div style={{ display: "grid", gap: compact ? 8 : 10 }}>
      {stages.map((stage, index) => (
        <div key={stage} className="msg-card" style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ display: "grid", placeItems: "center", width: 28, height: 28, borderRadius: 6, background: colors.saffron, color: colors.navy2, fontFamily: "var(--mono)", fontWeight: 600 }}>{index + 1}</span>
          <span>
            <strong style={{ display: "block" }}>{stage}</strong>
            <span style={{ color: colors.muted, fontSize: 12 }}>{index < 3 ? "AI verified" : "Human verification ready"}</span>
          </span>
        </div>
      ))}
    </div>
  );
}

export function DocumentPreview({ title = "Generated Complaint Draft" }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
      <div className="card">
        <p className="section-title" style={{ color: colors.green }}>Raw WhatsApp Conversation</p>
        <div className="msg-card" style={{ color: "#fff" }}>मुझे पिछले तीन महीने से सैलरी नहीं मिली। कंपनी बोल रही है बाद में देंगे।</div>
        <div className="msg-card" style={{ borderColor: "rgba(34,197,94,.25)", color: "rgba(255,255,255,.72)" }}>Hindi detected. Labour dispute identified. Missing salary slips and appointment proof.</div>
      </div>
      <div className="card2" style={{ animation: "doc-appear .35s ease" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, marginBottom: 12 }}>
          <p className="section-title" style={{ color: colors.saffron, marginBottom: 0 }}>{title}</p>
          <span className="badge badge-red" style={{ transform: "rotate(-5deg)" }}>COURT READY</span>
        </div>
        <div style={{ color: "rgba(255,255,255,.72)", display: "grid", gap: 8 }}>
          <p>To, The Labour Commissioner</p>
          <p>Subject: Complaint regarding unpaid wages for three months.</p>
          <p>The applicant respectfully submits that wages remain unpaid despite repeated reminders...</p>
          <strong style={{ color: "#fff" }}>Prayer: Direct release of pending wages with appropriate relief.</strong>
        </div>
      </div>
    </div>
  );
}

export function Disclaimer() {
  return (
    <div className="card" style={{ borderColor: "rgba(255,153,51,.25)", color: "rgba(255,255,255,.72)" }}>
      Generated content requires lawyer verification. NyayaSetu helps citizens prepare and organize information; it does not replace a lawyer or court order.
    </div>
  );
}
