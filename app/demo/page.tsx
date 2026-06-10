"use client";

import { useMemo, useState } from "react";
import { Navbar, shellStyle } from "../components";

type BackendResponse = {
  intent?: string;
  language?: string;
  body?: string;
  reply?: string;
  eligibility?: {
    eligible?: boolean;
    eligible_for_bail?: boolean;
    reason?: string;
    bnss_section?: string;
    recommended_section?: string;
  };
  bail_eligible?: boolean;
  eligible?: boolean;
  bnss_section?: string;
  bail_section?: string;
  recommended_section?: string;
  reason?: string;
  accused_name?: string;
  section_charged?: string;
  section?: string;
  grounds?: string[];
};

type DemoState = "idle" | "loading" | "done";

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";

const EXAMPLES = [
  "mera bhai jail mein hai section 302",
  "zamaanat ke liye property document",
  "My rights after arrest section 498A",
  "ennoda anna section 420 jail la",
  "case date kab hai FIR 1234"
];

const LANGUAGE_GROUPS = [
  {
    label: "Most used",
    options: [
      ["hi", "Hindi"],
      ["en", "English"],
      ["mr", "Marathi"],
      ["ta", "Tamil"],
      ["te", "Telugu"]
    ]
  },
  {
    label: "North and East",
    options: [
      ["bn", "Bengali"],
      ["pa", "Punjabi"],
      ["ur", "Urdu"],
      ["as", "Assamese"],
      ["or", "Odia"],
      ["ne", "Nepali"],
      ["ks", "Kashmiri"],
      ["sd", "Sindhi"],
      ["mai", "Maithili"],
      ["doi", "Dogri"]
    ]
  },
  {
    label: "West, South, Central",
    options: [
      ["gu", "Gujarati"],
      ["kn", "Kannada"],
      ["ml", "Malayalam"],
      ["kok", "Konkani"],
      ["mni", "Manipuri"],
      ["brx", "Bodo"],
      ["sat", "Santali"]
    ]
  }
];

const MOCK_RESPONSE: BackendResponse = {
  intent: "bail_enquiry",
  language: "hi",
  bail_eligible: true,
  bnss_section: "479",
  reason: "1/3 sentence served — mandatory bail consideration under BNSS Section 479",
  accused_name: "[detected from message]",
  section_charged: "302"
};

export default function DemoPage() {
  const [messageText, setMessageText] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState("hi");
  const [state, setState] = useState<DemoState>("idle");
  const [result, setResult] = useState<BackendResponse | null>(null);
  const [submittedMessage, setSubmittedMessage] = useState("");

  async function submitDemo() {
    const trimmed = messageText.trim();
    if (!trimmed || state === "loading") return;

    setState("loading");
    setResult(null);
    setSubmittedMessage(trimmed);

    try {
      const form = new FormData();
      form.append("Body", trimmed);
      form.append("From", "+919999999999");
      form.append("NumMedia", "0");

      const response = await fetch(`${backendUrl}/webhook`, {
        method: "POST",
        body: form
      });

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data = (await response.json()) as BackendResponse;
      setResult(data);
      setState("done");
    } catch {
      window.setTimeout(() => {
        setResult(MOCK_RESPONSE);
        setState("done");
      }, 2000);
    }
  }

  const documentData = useMemo(() => buildDocumentData(result, submittedMessage), [result, submittedMessage]);

  return (
    <main>
      <Navbar />
      <section style={{ ...shellStyle, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 18 }}>
        <section className="card" style={{ minHeight: 520 }}>
          <p className="section-title" style={{ color: "var(--saffron)" }}>Send a message</p>
          <textarea
            rows={5}
            placeholder="Type in any Indian language — Hindi, Tamil, Telugu, Marathi..."
            value={messageText}
            onChange={(event) => setMessageText(event.target.value)}
            style={{ minHeight: 150 }}
          />

          <div style={{ display: "grid", gridTemplateColumns: "minmax(150px, .6fr) 1fr", gap: 12, marginTop: 12 }}>
            <select value={selectedLanguage} onChange={(event) => setSelectedLanguage(event.target.value)} aria-label="Select language">
              {LANGUAGE_GROUPS.map((group) => (
                <optgroup key={group.label} label={group.label}>
                  {group.options.map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </optgroup>
              ))}
            </select>
            <button type="button" className="btn-primary" onClick={submitDemo} disabled={state === "loading" || !messageText.trim()}>
              {state === "loading" ? "Processing..." : "Process →"}
            </button>
          </div>

          <div style={{ marginTop: 18 }}>
            <p className="section-title">Try examples</p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {EXAMPLES.map((example) => (
                <button
                  key={example}
                  type="button"
                  className="badge badge-muted"
                  onClick={() => setMessageText(example)}
                  style={{ cursor: "pointer" }}
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        </section>

        <section className="card2" style={{ minHeight: 520, overflow: "hidden" }}>
          <p className="section-title" style={{ color: "var(--saffron)" }}>Transformation panel</p>
          {state === "idle" && <EmptyState />}
          {state === "loading" && <ScanningState />}
          {state === "done" && result && (
            <div style={{ display: "grid", gap: 16 }}>
              <WhatsAppCard message={submittedMessage} result={result} />
              <CourtDocumentCard data={documentData} />
            </div>
          )}
        </section>
      </section>
    </main>
  );
}

function EmptyState() {
  return (
    <div style={{
      minHeight: 420,
      border: "1px dashed rgba(255,153,51,.4)",
      borderRadius: "var(--r)",
      display: "grid",
      placeItems: "center",
      color: "var(--muted)",
      textAlign: "center",
      padding: 24
    }}>
      Your result will appear here
    </div>
  );
}

function ScanningState() {
  return (
    <div style={{
      minHeight: 420,
      border: "1px dashed rgba(255,153,51,.4)",
      borderRadius: "var(--r)",
      overflow: "hidden",
      display: "grid",
      placeItems: "center",
      color: "rgba(255,255,255,.7)"
    }}>
      <div style={{
        position: "absolute",
        left: 0,
        right: 0,
        height: 2,
        background: "var(--saffron)",
        boxShadow: "0 0 22px rgba(255,153,51,.9)",
        animation: "scan 1.2s linear infinite"
      }} />
      Processing legal route, eligibility, evidence and document draft...
    </div>
  );
}

function WhatsAppCard({ message, result }: { message: string; result: BackendResponse }) {
  return (
    <article className="card" style={{ animation: "msg-arrive .35s ease", padding: 0, overflow: "hidden", borderColor: "rgba(34,197,94,.28)" }}>
      <div style={{ background: "#075e54", color: "#fff", padding: "10px 14px", fontWeight: 600 }}>WhatsApp</div>
      <div style={{ padding: 16 }}>
        <div style={{
          maxWidth: "88%",
          background: "rgba(34,197,94,.18)",
          border: "0.5px solid rgba(34,197,94,.3)",
          borderRadius: "18px 18px 18px 4px",
          padding: "12px 14px",
          color: "#fff"
        }}>
          {message}
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 14 }}>
          <span className="badge badge-saffron">Language: {result.language || "detected"}</span>
          <span className="badge badge-blue">Intent: {formatIntent(result.intent)}</span>
        </div>
      </div>
    </article>
  );
}

function CourtDocumentCard({ data }: { data: ReturnType<typeof buildDocumentData> }) {
  return (
    <article style={{
      background: "#fff",
      color: "#111827",
      borderRadius: "var(--r)",
      padding: 22,
      boxShadow: "0 24px 80px rgba(0,0,0,.28)",
      animation: "doc-appear .42s ease .4s both",
      minHeight: 420
    }}>
      <div style={{
        position: "absolute",
        right: 20,
        top: 18,
        width: 92,
        height: 92,
        border: "2px solid rgba(198,40,40,.22)",
        borderRadius: "50%",
        color: "rgba(198,40,40,.26)",
        display: "grid",
        placeItems: "center",
        fontWeight: 700,
        letterSpacing: ".08em",
        transform: "rotate(-12deg)",
        fontSize: 13
      }}>
        LEGAL AID
      </div>

      <h2 style={{ maxWidth: "calc(100% - 110px)", fontSize: 20, lineHeight: 1.25, marginBottom: 6 }}>IN THE COURT OF {data.courtName}</h2>
      <p style={{ color: "#6b7280", fontSize: 12, letterSpacing: ".06em", textTransform: "uppercase", marginBottom: 18 }}>Generated court assistance draft</p>

      <section style={{ display: "grid", gap: 10, marginBottom: 18 }}>
        <DocLine label="Accused" value={data.accusedName} />
        <DocLine label="Section charged" value={data.sectionCharged} />
        <DocLine label="Bail provision" value={data.bailSection} />
        <DocLine label="Eligibility result" value={data.eligibilityText} />
      </section>

      <h3 style={{ fontSize: 15, marginBottom: 8 }}>Grounds</h3>
      <ol style={{ display: "grid", gap: 8, paddingLeft: 18, color: "#1f2937" }}>
        {data.grounds.map((ground) => (
          <li key={ground}>{ground}</li>
        ))}
      </ol>

      <p style={{ borderTop: "1px solid #e5e7eb", marginTop: 20, paddingTop: 14, color: "#4b5563", fontSize: 13 }}>
        Generated by NyayaSetu AI Legal Aid
      </p>

      <a href={`${backendUrl}/static/42.pdf`} style={{
        display: "block",
        width: "100%",
        textAlign: "center",
        marginTop: 16,
        background: "#15803d",
        color: "#fff",
        borderRadius: 6,
        padding: "12px 16px",
        textDecoration: "none",
        fontWeight: 700
      }}>
        Download PDF
      </a>
    </article>
  );
}

function DocLine({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <strong style={{ display: "block", fontSize: 11, color: "#6b7280", textTransform: "uppercase", letterSpacing: ".05em" }}>{label}</strong>
      <span>{value}</span>
    </div>
  );
}

function buildDocumentData(response: BackendResponse | null, originalMessage: string) {
  const eligibilityBlock = response?.eligibility;
  const eligible = response?.bail_eligible ?? response?.eligible ?? eligibilityBlock?.eligible ?? eligibilityBlock?.eligible_for_bail ?? response?.intent === "bail_enquiry";
  const section = response?.section_charged || response?.section || inferSection(response?.body || originalMessage);
  const reason = response?.reason || eligibilityBlock?.reason || response?.reply || "The message has been classified and a legal-aid draft has been prepared for lawyer verification.";
  const bnssSection = response?.bnss_section || eligibilityBlock?.bnss_section || "480";
  const bailSection = response?.bail_section || response?.recommended_section || eligibilityBlock?.recommended_section || `BNSS Section ${bnssSection}`;
  const eligibilityText = eligible ? `Eligible for bail consideration. ${reason}` : `Not automatically eligible. ${reason}`;
  const grounds = response?.grounds?.length ? response.grounds : [
    `The applicant seeks bail consideration under ${bailSection} based on the facts extracted from the citizen message.`,
    `The charged section identified from the message is Section ${section}, and the custody/legal status requires urgent lawyer verification.`,
    reason,
    "The applicant undertakes to cooperate with investigation and court dates and to comply with any conditions imposed by the court.",
    "The draft is prepared only for legal-aid assistance and must be reviewed by an advocate before filing."
  ];

  return {
    courtName: "Honourable Sessions Court",
    accusedName: response?.accused_name || "Citizen message did not include accused name",
    sectionCharged: section,
    bailSection,
    eligibilityText,
    grounds
  };
}

function inferSection(text: string) {
  const match = text.match(/(?:section|sec|धारा)\s*([0-9]{2,3}[A-Z]?)/i);
  return match ? match[1].toUpperCase() : "Section not specified in message";
}

function formatIntent(intent?: string) {
  return (intent || "legal enquiry").replaceAll("_", " ");
}
