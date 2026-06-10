import { Disclaimer, JourneyEngine, Navbar, PageHero, ScoreRing, shellStyle } from "../components";

const checklist = [
  ["FIR copy", "received"],
  ["Arrest memo", "missing"],
  ["Custody proof", "received"],
  ["Surety ID", "needed"],
  ["Property document", "ready"],
  ["Lawyer verification", "pending"]
];

const grounds = [
  "The alleged offence under Section 420 IPC is non-bailable but triable with conditions under Section 437/439 CrPC and Section 480/481 BNSS.",
  "The applicant has remained in custody for a material period and undertakes to cooperate with investigation and trial.",
  "The applicant is willing to furnish surety and comply with attendance, travel, and witness-protection conditions.",
  "The applicant shall not tamper with evidence or influence witnesses.",
  "Further incarceration is not necessary if the court imposes appropriate safeguards."
];

export default function ZamanatPage() {
  return (
    <main>
      <Navbar />
      <section style={shellStyle}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16, marginBottom: 16 }}>
          <div style={{ display: "grid", gap: 16 }}>
            <PageHero kicker="ZamanatAI Module" title="Arrest-to-bail workflow that families can understand.">
              FIR sections, bailable status, custody thresholds, required documents, bail application, and surety bond drafts in one court-ready package.
            </PageHero>
            <section className="card">
              <h2 className="section-title">Bail Journey</h2>
              <JourneyEngine compact />
            </section>
          </div>
          <section className="card2">
            <ScoreRing score={88} label="Bail Readiness" />
            <div className="card" style={{ marginTop: 16, textAlign: "center" }}>
              <div className="section-title">FIR Upload Mock</div>
              <div className="stat-num" style={{ fontSize: 30 }}>FIR 42/2024</div>
              <p style={{ color: "var(--muted)" }}>Sections extracted: 420 IPC, custody 3 months</p>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: 10, marginTop: 12 }}>
              <Status label="Bailable" value="No" tone="danger" />
              <Status label="Recommended" value="439 CrPC / 481 BNSS" tone="success" />
            </div>
          </section>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 16 }}>
          <section className="card">
            <h2 style={{ marginBottom: 12 }}>Surety Checklist</h2>
            {checklist.map(([item, status]) => (
              <div key={item} className="msg-card" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10 }}>
                <strong>{item}</strong>
                <span className={`badge ${status === "received" || status === "ready" ? "badge-green" : status === "missing" ? "badge-red" : "badge-saffron"}`}>{status}</span>
              </div>
            ))}
          </section>

          <section className="card">
            <h2 style={{ marginBottom: 12 }}>Bail Grounds Generated</h2>
            <div style={{ display: "grid", gap: 10 }}>
              {grounds.map((ground, index) => (
                <div key={ground} className="msg-card" style={{ color: "rgba(255,255,255,.74)" }}>
                  <strong style={{ color: "var(--saffron)" }}>{index + 1}. </strong>{ground}
                </div>
              ))}
            </div>
          </section>

          <section style={{ display: "grid", gap: 16 }}>
            <div className="card">
              <h2 style={{ marginBottom: 12 }}>Court-Ready Package</h2>
              <Preview title="Bail Application Preview" />
              <div style={{ height: 12 }} />
              <Preview title="Surety Bond Preview" />
            </div>
            <Disclaimer />
          </section>
        </div>
      </section>
    </main>
  );
}

function Status({ label, value, tone }) {
  return (
    <div className="card">
      <div className="section-title" style={{ marginBottom: 4 }}>{label}</div>
      <span className={`badge ${tone === "danger" ? "badge-red" : "badge-green"}`}>{value}</span>
    </div>
  );
}

function Preview({ title }) {
  return (
    <div className="card2">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, marginBottom: 12 }}>
        <div className="section-title" style={{ color: "var(--saffron)", marginBottom: 0 }}>{title}</div>
        <span className="badge badge-red" style={{ transform: "rotate(-5deg)" }}>DRAFT</span>
      </div>
      <div style={{ display: "grid", gap: 8 }}>
        {[75, 100, 84, 66].map((width) => (
          <div key={width} style={{ height: 6, width: `${width}%`, borderRadius: 3, background: "rgba(255,255,255,.14)" }} />
        ))}
      </div>
    </div>
  );
}
