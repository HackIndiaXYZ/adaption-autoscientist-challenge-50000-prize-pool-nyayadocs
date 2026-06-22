"use client";

import { useMemo, useState } from "react";
import { Disclaimer, Navbar, shellStyle } from "../components";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";

type ServiceType = "income_certificate" | "caste_certificate" | "domicile_certificate" | "disability_pension" | "legal_aid_application";

type ServiceConfig = {
  name: string;
  authority: string;
  fields: string[];
  documents: string[];
};

const SERVICES: Record<ServiceType, ServiceConfig> = {
  income_certificate: {
    name: "Income Certificate",
    authority: "Revenue Department / Tehsildar",
    fields: ["applicant_name", "date_of_birth", "address", "district", "state", "annual_family_income", "purpose"],
    documents: ["identity_proof", "address_proof", "income_proof", "passport_photo", "self_declaration"]
  },
  caste_certificate: {
    name: "Caste Certificate",
    authority: "Revenue / Social Justice Department",
    fields: ["applicant_name", "date_of_birth", "address", "district", "state", "category", "caste_name", "father_or_guardian_name"],
    documents: ["identity_proof", "address_proof", "birth_or_school_record", "family_caste_evidence", "passport_photo", "self_declaration"]
  },
  domicile_certificate: {
    name: "Domicile / Residence",
    authority: "Revenue Department / District Administration",
    fields: ["applicant_name", "date_of_birth", "current_address", "district", "state", "years_of_residence", "purpose"],
    documents: ["identity_proof", "address_proof", "residence_history", "passport_photo", "self_declaration"]
  },
  disability_pension: {
    name: "Disability Pension",
    authority: "Social Welfare Department",
    fields: ["applicant_name", "date_of_birth", "address", "district", "state", "disability_type", "disability_percentage", "bank_account_last4"],
    documents: ["identity_proof", "address_proof", "disability_certificate", "bank_passbook", "passport_photo"]
  },
  legal_aid_application: {
    name: "Free Legal Aid",
    authority: "District / State Legal Services Authority",
    fields: ["applicant_name", "address", "district", "state", "legal_issue", "opposite_party", "case_or_fir_number", "income_or_eligibility_basis"],
    documents: ["identity_proof", "address_proof", "case_document", "income_or_category_proof"]
  }
};

const LABELS: Record<string, string> = {
  applicant_name: "Applicant name",
  date_of_birth: "Date of birth",
  address: "Permanent address",
  current_address: "Current address",
  district: "District",
  state: "State",
  annual_family_income: "Annual family income (INR)",
  purpose: "Purpose of application",
  category: "Category (SC / ST / OBC / EWS)",
  caste_name: "Caste / community name",
  father_or_guardian_name: "Father / guardian name",
  years_of_residence: "Years of residence",
  disability_type: "Disability type",
  disability_percentage: "Disability percentage",
  bank_account_last4: "Bank account last 4 digits",
  legal_issue: "Legal issue",
  opposite_party: "Opposite party",
  case_or_fir_number: "Case / FIR number",
  income_or_eligibility_basis: "Income or eligibility basis"
};

type OcrResult = {
  document_type: string;
  fields: Record<string, string>;
  confidence: Record<string, number>;
  overall_confidence: number;
  requires_confirmation: boolean;
};

type Assessment = {
  readiness_score: number;
  status: string;
  issuing_authority: string;
  missing_fields: string[];
  missing_documents: string[];
  conditional_documents: string[];
  mismatches: Array<{ field: string }>;
  blockers: string[];
  next_steps: string[];
  disclaimer: string;
};

export default function CivicDocsPage() {
  const [serviceType, setServiceType] = useState<ServiceType>("income_certificate");
  const [applicant, setApplicant] = useState<Record<string, string>>({});
  const [documents, setDocuments] = useState<string[]>([]);
  const [ocrResults, setOcrResults] = useState<OcrResult[]>([]);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [loading, setLoading] = useState<"ocr" | "assess" | "pdf" | null>(null);
  const [error, setError] = useState("");

  const service = SERVICES[serviceType];
  const completedFields = useMemo(
    () => service.fields.filter((field) => applicant[field]?.trim()).length,
    [applicant, service.fields]
  );

  function changeService(next: ServiceType) {
    setServiceType(next);
    setApplicant({});
    setDocuments([]);
    setOcrResults([]);
    setAssessment(null);
    setError("");
  }

  function toggleDocument(document: string) {
    setDocuments((current) => current.includes(document) ? current.filter((item) => item !== document) : [...current, document]);
  }

  async function uploadForOcr(file: File | undefined) {
    if (!file) return;
    setLoading("ocr");
    setError("");
    const form = new FormData();
    form.append("file", file);
    form.append("document_type", file.name.replace(/\.[^.]+$/, ""));
    try {
      const response = await fetch(`${BACKEND}/civicdocs/ocr`, { method: "POST", body: form });
      if (!response.ok) throw new Error((await response.json()).detail || "OCR failed");
      const result: OcrResult = await response.json();
      setOcrResults((current) => [...current, result]);
      setApplicant((current) => {
        const merged = { ...current };
        Object.entries(result.fields).forEach(([field, value]) => {
          if (value && !merged[field]) merged[field] = value;
        });
        return merged;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not process this image");
    } finally {
      setLoading(null);
    }
  }

  function payload() {
    return {
      service_type: serviceType,
      applicant_data: applicant,
      available_documents: documents,
      extracted_documents: ocrResults
    };
  }

  async function assess() {
    setLoading("assess");
    setError("");
    try {
      const response = await fetch(`${BACKEND}/civicdocs/assess`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload())
      });
      if (!response.ok) throw new Error((await response.json()).detail || "Assessment failed");
      setAssessment(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not assess this application");
    } finally {
      setLoading(null);
    }
  }

  async function downloadPacket() {
    setLoading("pdf");
    setError("");
    try {
      const response = await fetch(`${BACKEND}/civicdocs/generate-packet`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...payload(), preferred_language: "en" })
      });
      if (!response.ok) throw new Error((await response.json()).detail || "PDF generation failed");
      const blob = await response.blob();
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `civicdocs_${serviceType}.pdf`;
      link.click();
      URL.revokeObjectURL(link.href);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate packet");
    } finally {
      setLoading(null);
    }
  }

  return (
    <main>
      <Navbar />
      <section style={shellStyle}>
        <header style={{ padding: "18px 0 22px", borderBottom: "1px solid var(--border)", marginBottom: 18 }}>
          <div className="section-title" style={{ color: "var(--saffron)" }}>CivicDocs · Public Service Access</div>
          <h1 style={{ fontSize: "clamp(30px, 5vw, 52px)", maxWidth: 900, lineHeight: 1.08 }}>Turn document photos into a verified application path.</h1>
          <p style={{ color: "var(--muted)", maxWidth: 780, marginTop: 10 }}>
            OCR-assisted application preparation for income, caste, domicile, disability pension, and free legal aid. CivicDocs prepares the packet; only the authorised authority can issue or approve it.
          </p>
        </header>

        <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1.15fr) minmax(290px,.85fr)", gap: 16 }} className="civic-layout">
          <section style={{ display: "grid", gap: 16 }}>
            <div className="card2">
              <div className="section-title">1 · Select service</div>
              <div className="service-tabs">
                {(Object.keys(SERVICES) as ServiceType[]).map((key) => (
                  <button key={key} type="button" onClick={() => changeService(key)} className={`service-tab ${serviceType === key ? "active" : ""}`}>
                    {SERVICES[key].name}
                  </button>
                ))}
              </div>
              <p style={{ marginTop: 12, color: "var(--muted)" }}>Authorised route: {service.authority}</p>
            </div>

            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", marginBottom: 12 }}>
                <div className="section-title" style={{ marginBottom: 0 }}>2 · Applicant details</div>
                <span className="badge badge-saffron">{completedFields}/{service.fields.length} complete</span>
              </div>
              <div className="field-grid">
                {service.fields.map((field) => (
                  <label key={field}>
                    <span>{LABELS[field] || field.replaceAll("_", " ")}</span>
                    <input
                      value={applicant[field] || ""}
                      onChange={(event) => setApplicant((current) => ({ ...current, [field]: event.target.value }))}
                      placeholder={`Enter ${(LABELS[field] || field).toLowerCase()}`}
                    />
                  </label>
                ))}
              </div>
            </div>

            <div className="card">
              <div className="section-title">3 · Evidence and OCR</div>
              <div className="document-checklist">
                {service.documents.map((item) => (
                  <label key={item} className="document-row">
                    <input type="checkbox" checked={documents.includes(item)} onChange={() => toggleDocument(item)} />
                    <span>{item.replaceAll("_", " ")}</span>
                  </label>
                ))}
              </div>
              <label className="upload-zone">
                <strong>{loading === "ocr" ? "Scanning document..." : "Upload document image for OCR"}</strong>
                <span>JPG or PNG · fields remain reviewable before use</span>
                <input type="file" accept="image/*" onChange={(event) => uploadForOcr(event.target.files?.[0])} disabled={loading === "ocr"} />
              </label>
              {ocrResults.map((result, index) => (
                <div key={`${result.document_type}-${index}`} className="ocr-result">
                  <div><strong>{result.document_type}</strong><span className={`badge ${result.requires_confirmation ? "badge-red" : "badge-green"}`}>{Math.round(result.overall_confidence * 100)}% OCR</span></div>
                  <p>{Object.values(result.fields).filter(Boolean).length} fields extracted · {result.requires_confirmation ? "confirmation required" : "ready for review"}</p>
                </div>
              ))}
            </div>

            {error && <div className="card" style={{ borderColor: "rgba(239,68,68,.45)", color: "#fca5a5" }}>{error}</div>}
            <button className="btn-primary" onClick={assess} disabled={loading !== null}>{loading === "assess" ? "Checking application..." : "Check application readiness"}</button>
          </section>

          <aside style={{ display: "grid", gap: 16, alignContent: "start" }}>
            <section className="readiness-panel">
              <div className="section-title">Application readiness</div>
              <div className="readiness-number">{assessment?.readiness_score ?? 0}<span>%</span></div>
              <div className="readiness-track"><span style={{ width: `${assessment?.readiness_score ?? 0}%` }} /></div>
              <p>{assessment ? assessment.status.replaceAll("_", " ") : "Complete details and evidence to calculate readiness."}</p>
            </section>

            {assessment && (
              <>
                <section className="card">
                  <div className="section-title">Missing or blocked</div>
                  {[...assessment.missing_fields.map((item) => `Field: ${item}`), ...assessment.missing_documents.map((item) => `Document: ${item}`), ...assessment.mismatches.map((item) => `Mismatch: ${item.field}`)].map((item) => (
                    <div className="issue-row" key={item}><span>!</span>{item.replaceAll("_", " ")}</div>
                  ))}
                  {!assessment.missing_fields.length && !assessment.missing_documents.length && !assessment.mismatches.length && <div className="issue-row success"><span>✓</span>No mandatory blockers detected</div>}
                </section>
                <section className="card">
                  <div className="section-title">Official route</div>
                  <strong>{assessment.issuing_authority}</strong>
                  {assessment.next_steps.map((step, index) => <div className="next-step" key={step}><span>{index + 1}</span>{step}</div>)}
                </section>
                <button className="btn-primary" onClick={downloadPacket} disabled={loading !== null}>{loading === "pdf" ? "Preparing PDF..." : "Download application packet"}</button>
              </>
            )}
            <Disclaimer />
          </aside>
        </div>
      </section>
    </main>
  );
}
