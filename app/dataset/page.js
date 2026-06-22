import { Navbar, PageHero, shellStyle } from "../components";

const languages = [
  ["Hindi", 24],
  ["English", 20],
  ["Tamil", 12],
  ["Marathi", 10],
  ["Bengali", 9],
  ["Telugu", 9],
  ["Other Indian languages", 16]
];

const samples = [
  ["Legal Aid", "Salary Dispute", "Missing salary slip added to evidence checklist"],
  ["ZamanatAI", "Bail Enquiry", "Custody period normalized and surety evidence requested"],
  ["CivicDocs", "Income Certificate", "OCR name mismatch marked for confirmation"],
  ["CivicDocs", "Disability Pension", "Medical certificate and bank proof identified as mandatory"]
];

export default function DatasetPage() {
  return (
    <main>
      <Navbar />
      <section style={shellStyle}>
        <PageHero kicker="Adaptive Data Engine" title="Every correction improves the justice map.">
          One balanced dataset trains Legal Aid, ZamanatAI, and CivicDocs across intent classification, safe response generation, OCR correction, missing-document detection, and application readiness.
        </PageHero>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16, marginTop: 16 }}>
          <section className="card">
            <h2 style={{ marginBottom: 12 }}>Adaptive Metrics</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: 10 }}>
              {[
                ["Unified Records", "2,451"],
                ["Held-out Test Rows", "239"],
                ["CivicDocs Records", "900"],
                ["Modules", "3"]
              ].map(([label, value]) => (
                <div key={label} className="card2">
                  <div className="stat-num">{value}</div>
                  <div className="stat-label">{label}</div>
                </div>
              ))}
            </div>
            <a href="https://huggingface.co/datasets/Ananya80/nyayasetu-legal-dialogues-multilingual" className="btn-primary" style={{ display: "inline-block", width: "auto", textDecoration: "none", marginTop: 16 }}>
              Download Dataset
            </a>
          </section>

          <section className="card">
            <h2 style={{ marginBottom: 12 }}>Language Distribution</h2>
            <div style={{ display: "grid", gap: 12 }}>
              {languages.map(([name, value]) => (
                <div key={name}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 5 }}>
                    <strong>{name}</strong>
                    <span style={{ color: "var(--muted)" }}>{value}%</span>
                  </div>
                  <div style={{ height: 4, borderRadius: 2, background: "rgba(255,255,255,.08)" }}>
                    <div className="lang-bar-fill" style={{ "--w": `${value}%`, background: "var(--saffron)" }} />
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16, marginTop: 16 }}>
          <section className="card">
            <h2 style={{ marginBottom: 12 }}>Sample Anonymised Interactions</h2>
            {samples.map(([language, issue, correction]) => (
              <div key={correction} className="msg-card">
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10 }}>
                  <strong>{issue}</strong>
                  <span className="badge badge-saffron">{language}</span>
                </div>
                <p style={{ marginTop: 8, color: "rgba(255,255,255,.68)" }}>{correction}</p>
              </div>
            ))}
          </section>

          <section className="card">
            <h2 style={{ marginBottom: 12 }}>Feedback Corrections</h2>
            {[
              "Police station extraction improved for Hindi abbreviations",
              "Bail urgency tuned using custody duration",
              "Property OCR confidence now asks for confirmation below 75%",
              "CivicDocs stores redacted field corrections without retaining personal values"
            ].map((item) => (
              <div key={item} className="msg-card" style={{ display: "flex", gap: 10, alignItems: "center" }}>
                <span className="badge badge-green">✓</span>
                <strong>{item}</strong>
              </div>
            ))}
          </section>
        </div>
      </section>
    </main>
  );
}
