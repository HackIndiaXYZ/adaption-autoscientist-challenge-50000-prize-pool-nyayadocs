"use client";

import { useEffect, useState } from "react";
import { Disclaimer, DocumentPreview, JourneyEngine, PageHero, ScoreRing, shellStyle } from "./components";

type Message = {
  id: number;
  input_text: string;
  input_language: string;
  language_name: string;
  intent: string;
  has_pdf: boolean;
  timestamp?: string;
};

type LangTickerItem = {
  lang: string;
  flag: string;
  code: string;
};

type Stats = {
  total: number;
  languages: number;
  docs: number;
  rows: number;
};

type WebSocketPayload = {
  type?: string;
  input_text?: string;
  input_language?: string;
  language_name?: string;
  intent?: string;
  has_pdf?: boolean;
  timestamp?: string;
};

const MOCK_MESSAGES: Message[] = [
  { id: 1, input_text: "mera bhai jail mein hai section 302 FIR 1234 thana hazratganj 8 mahine se", input_language: "hi", language_name: "Hindi", intent: "bail_enquiry", has_pdf: true },
  { id: 2, input_text: "ennoda anna jail la irukkan section 420 FIR 5678 2 month aachu", input_language: "ta", language_name: "Tamil", intent: "bail_enquiry", has_pdf: true },
  { id: 3, input_text: "zamaanat ke liye kya documents chahiye court mein submission", input_language: "hi", language_name: "Hindi", intent: "surety_bond", has_pdf: false },
  { id: 4, input_text: "My brother in custody 4 months section 498A what are his legal rights", input_language: "en", language_name: "English", intent: "legal_rights", has_pdf: false },
  { id: 5, input_text: "naa akka case status enti FIR 9012 vishakhapatnam police station lo", input_language: "te", language_name: "Telugu", intent: "case_status", has_pdf: false },
  { id: 6, input_text: "aama maza dada jail madhe ahe section 379 bail milel ka 3 mahine zale", input_language: "mr", language_name: "Marathi", intent: "bail_enquiry", has_pdf: true }
];

const INITIAL_LANG_TICKER: LangTickerItem[] = [
  { lang: "Hindi", flag: "🇮🇳", code: "hi" },
  { lang: "Tamil", flag: "🇮🇳", code: "ta" },
  { lang: "Telugu", flag: "🇮🇳", code: "te" },
  { lang: "Marathi", flag: "🇮🇳", code: "mr" },
  { lang: "English", flag: "🇬🇧", code: "en" },
  { lang: "Bengali", flag: "🇮🇳", code: "bn" }
];

const LANG_COLORS: Record<string, string> = {
  hi: "badge-saffron",
  ta: "badge-purple",
  te: "badge-blue",
  mr: "badge-green",
  en: "badge-muted",
  bn: "badge-blue",
  default: "badge-muted"
};

const INTENT_COLORS: Record<string, string> = {
  bail_enquiry: "badge-saffron",
  surety_bond: "badge-green",
  case_status: "badge-muted",
  legal_rights: "badge-blue"
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>(MOCK_MESSAGES);
  const [isLive, setIsLive] = useState(false);
  const [stats, setStats] = useState<Stats>({ total: 6, languages: 3, docs: 3, rows: 6 });
  const [langTicker, setLangTicker] = useState<LangTickerItem[]>(INITIAL_LANG_TICKER);

  useEffect(() => {
    let connected = false;
    let mockIdx = 0;
    const mockTimer = window.setInterval(() => {
      if (connected) return;
      mockIdx = (mockIdx + 1) % MOCK_MESSAGES.length;
      const rotated = [...MOCK_MESSAGES.slice(mockIdx), ...MOCK_MESSAGES.slice(0, mockIdx)];
      setMessages(rotated);
    }, 3500);

    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
    const wsUrl = backendUrl.replace("http", "ws") + "/ws";
    let ws: WebSocket | null = null;

    try {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => {
        connected = true;
        setIsLive(true);
        window.clearInterval(mockTimer);
      };
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data) as WebSocketPayload;
        if (data.type === "new_message") {
          const nextMessage: Message = {
            id: Date.now(),
            input_text: data.input_text || "",
            input_language: data.input_language || "en",
            language_name: data.language_name || data.input_language || "Unknown",
            intent: data.intent || "legal_rights",
            has_pdf: Boolean(data.has_pdf),
            timestamp: data.timestamp
          };
          setMessages((prev) => [nextMessage, ...prev].slice(0, 8));
          setLangTicker((prev) => [
            {
              lang: nextMessage.language_name,
              flag: nextMessage.input_language === "en" ? "🇬🇧" : "🇮🇳",
              code: nextMessage.input_language
            },
            ...prev
          ].slice(0, 12));
          setStats((prev) => ({
            total: prev.total + 1,
            languages: prev.languages,
            docs: nextMessage.has_pdf ? prev.docs + 1 : prev.docs,
            rows: prev.rows + 1
          }));
        }
      };
      ws.onclose = () => {
        connected = false;
        setIsLive(false);
      };
    } catch {
      connected = false;
    }

    return () => {
      window.clearInterval(mockTimer);
      ws?.close();
    };
  }, []);

  const impactStats = [
    ["Citizens Assisted", stats.total, stats.total.toLocaleString()],
    ["Documents Generated", stats.docs, stats.docs.toLocaleString()],
    ["Dataset Rows", stats.rows, stats.rows.toLocaleString()],
    ["Languages Active", stats.languages, `${stats.languages}+`]
  ] as const;

  return (
    <main>
      <DashboardNavbar isLive={isLive} />
      <section style={{ ...shellStyle, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16 }}>
        <aside className="card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, marginBottom: 14 }}>
            <h2 className="section-title" style={{ marginBottom: 0 }}>Live Citizen Request Feed</h2>
            <span className={`badge ${isLive ? "badge-green" : "badge-saffron"}`}>
              {isLive ? <span className="live-dot" /> : null}
              {isLive ? "WebSocket Live" : "Demo Feed"}
            </span>
          </div>
          <LanguageTicker items={langTicker} />
          {messages.map((message, index) => (
            <MessageCard key={message.id} message={message} index={index} />
          ))}
        </aside>

        <section style={{ display: "grid", gap: 16 }}>
          <PageHero kicker="Google Maps for Justice" title="WhatsApp voice -> Justice path -> Court-ready document in 60 seconds">
            NyayaSetu AI turns a citizen&apos;s raw message into language detection, legal intent, evidence gaps, readiness score, and verified document workflows.
          </PageHero>
          <div className="card2" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 14 }}>
            <HeroAnimation />
            <div className="card">
              <ScoreRing score={82} />
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: 8, marginTop: 14 }}>
                {["Evidence 90%", "Documents 75%", "Witness 70%", "Submission 80%"].map((item) => (
                  <span key={item} className="badge badge-muted">{item}</span>
                ))}
              </div>
            </div>
          </div>
          <section className="card">
            <h2 style={{ marginBottom: 14 }}>Justice Journey Engine</h2>
            <JourneyEngine />
          </section>
        </section>

        <aside style={{ display: "grid", gap: 16 }}>
          <div className="card">
            <h2 className="section-title">Document Preview</h2>
            <DocumentPreview />
          </div>
          <div className="card">
            <h2 className="section-title">Impact Dashboard</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: 10 }}>
              {impactStats.map(([label, value, displayValue]) => (
                <div key={label} className="card2">
                  <div className="stat-num" key={value} style={{ animation: "counter-up .3s ease" }}>{displayValue}</div>
                  <div className="stat-label">{label}</div>
                </div>
              ))}
            </div>
          </div>
          <Disclaimer />
        </aside>
      </section>
      <section style={{ ...shellStyle, paddingTop: 0 }}>
        <div className="module-strip">
          {[
            ["NyayaSetu Legal Aid", "Legal rights, case status, labour, tenancy, cyber fraud and free legal aid.", "/demo", "LEGAL"],
            ["ZamanatAI", "Bail eligibility, bail application and surety-bond preparation.", "/zamanat", "BAIL"],
            ["CivicDocs", "OCR-assisted income, caste, domicile, disability and legal-aid application packets.", "/civicdocs", "CIVIC"]
          ].map(([title, description, href, badge]) => (
            <a href={href} key={title} className="module-link">
              <span className="badge badge-saffron">{badge}</span>
              <strong>{title}</strong>
              <p>{description}</p>
              <span>Open workflow →</span>
            </a>
          ))}
        </div>
      </section>
      <BottomMarquee />
    </main>
  );
}

function DashboardNavbar({ isLive }: { isLive: boolean }) {
  return (
    <nav>
      <span className="nav-logo">⚖ NyayaSetu</span>
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <span className="live-dot"></span>
        <span style={{ fontSize: "11px", fontWeight: 600, letterSpacing: ".06em", color: isLive ? "var(--green)" : "var(--muted)" }}>
          {isLive ? "LIVE" : "DEMO MODE"}
        </span>
      </div>
      <div className="nav-links">
        <a href="/" className="active">Dashboard</a>
        <a href="/demo">Try it</a>
        <a href="/zamanat">ZamanatAI</a>
        <a href="/civicdocs">CivicDocs</a>
        <a href="/dataset">Dataset</a>
      </div>
    </nav>
  );
}

function LanguageTicker({ items }: { items: LangTickerItem[] }) {
  return (
    <div style={{ display: "flex", gap: "8px", overflowX: "hidden", marginBottom: "16px", maskImage: "linear-gradient(to right, transparent, black 10%, black 90%, transparent)" }}>
      {items.map((item, index) => (
        <span key={`${item.code}-${index}`} className={`badge ${LANG_COLORS[item.code] || "badge-muted"}`} style={{ whiteSpace: "nowrap", animation: index === 0 ? "slide-down .3s ease" : "none" }}>
          {item.flag} {item.lang}
        </span>
      ))}
    </div>
  );
}

function MessageCard({ message, index }: { message: Message; index: number }) {
  const text = truncate(message.input_text || "", 70);
  const languageClass = LANG_COLORS[message.input_language] || LANG_COLORS.default;
  const intentClass = INTENT_COLORS[message.intent] || "badge-muted";

  return (
    <div key={message.id} className="msg-card">
      <div style={{ display: "grid", gridTemplateColumns: "34px 1fr auto", gap: 10, alignItems: "start" }}>
        <div style={{ width: 34, height: 34, borderRadius: "50%", background: "#22c55e", color: "#08200f", display: "grid", placeItems: "center", fontWeight: 700 }}>W</div>
        <div style={{ minWidth: 0 }}>
          <p style={{ color: "rgba(255,255,255,.82)", overflowWrap: "anywhere" }}>{text}</p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8 }}>
            <span className={`badge ${languageClass}`}>{message.language_name || message.input_language}</span>
            <span className={`badge ${intentClass}`}>{formatIntent(message.intent)}</span>
            <span className="badge badge-muted">{message.timestamp ? formatAgo(message.timestamp) : `${index + 1}m ago`}</span>
          </div>
        </div>
        {message.has_pdf ? <span className="badge badge-green">PDF ✓</span> : null}
      </div>
    </div>
  );
}

function HeroAnimation() {
  const steps = ["Hindi Detected", "Labour Dispute", "Evidence 4/7", "Readiness 68%", "Draft Generated"];
  return (
    <div className="card" style={{ minHeight: 300, animation: "doc-appear .4s ease" }}>
      <div className="msg-card" style={{ maxWidth: "82%", background: "rgba(34,197,94,.16)", borderColor: "rgba(34,197,94,.3)" }}>
        मुझे पिछले तीन महीने से सैलरी नहीं मिली
      </div>
      <div style={{ display: "grid", gap: 8 }}>
        {steps.map((step) => (
          <div key={step} className="msg-card" style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span className="badge badge-green">✓</span>
            <strong>{step}</strong>
          </div>
        ))}
      </div>
      <div className="card2" style={{ marginTop: 14 }}>
        <p className="section-title" style={{ color: "var(--saffron)" }}>Stamped Court Document</p>
        <div style={{ height: 6, width: "75%", borderRadius: 3, background: "rgba(255,255,255,.14)" }} />
        <div style={{ height: 6, width: "50%", borderRadius: 3, background: "rgba(255,255,255,.14)", marginTop: 8 }} />
        <span className="badge badge-red" style={{ marginTop: 14, transform: "rotate(-5deg)" }}>READY</span>
      </div>
    </div>
  );
}

function BottomMarquee() {
  return (
    <div style={{
      borderTop: "0.5px solid var(--border)",
      background: "var(--navy2)",
      overflow: "hidden",
      padding: "10px 0",
      whiteSpace: "nowrap"
    }}>
      <div style={{ display: "inline-block", animation: "marquee 25s linear infinite" }}>
        {"  ⚖ NyayaSetu + ZamanatAI  ·  WhatsApp → Court Document in 60s  ·  22 Indian languages  ·  Zero cost to families  ·  Built for HackIndia 2026  ·  Adaptive Data Track  ·  242 languages supported  ·  Dataset: nyayasetu-legal-dialogues-multilingual  ·  ".repeat(3)}
      </div>
    </div>
  );
}

function truncate(value: string, limit: number) {
  return value.length > limit ? `${value.slice(0, limit - 1)}…` : value;
}

function formatIntent(intent: string) {
  return String(intent || "unknown").replaceAll("_", " ");
}

function formatAgo(timestamp: string) {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(timestamp).getTime()) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  return `${Math.floor(minutes / 60)}h ago`;
}
