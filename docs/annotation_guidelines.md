# NyayaSetu Annotation Guidelines

## Purpose

Annotate multilingual citizen requests for the NyayaSetu Unified Intake Model. Annotators must classify the request, extract only supported entities, identify missing information/documents, and preserve legal safety boundaries.

## Unit Of Annotation

One row represents one citizen request plus optional OCR text and available-document list. Do not combine unrelated requests into one row.

## Required Labels

1. `module`: `legal_aid`, `zamanatai`, or `civicdocs`.
2. `intent`: choose exactly one primary intent from `data/label_definitions.json`.
3. `urgency`: `low`, `medium`, `high`, or `emergency`.
4. `entities`: include only values explicitly present in the message/OCR.
5. `missing_information`: facts required to continue safely.
6. `missing_documents`: evidence required for the workflow but not supplied.
7. `next_actions`: ordered, practical and authority-safe.
8. `safety_boundary`: state who must verify or decide the outcome.

## Module Rules

### Legal Aid

Use for legal rights, status, labour, tenancy, cyber fraud, consumer, domestic violence, RTI, and police refusal. If the user explicitly asks for bail or surety, use ZamanatAI instead.

### ZamanatAI

Use for bail eligibility, bail applications, custody thresholds, surety, bond, or property evidence for bail. Never label bail as guaranteed.

### CivicDocs

Use for income, caste, domicile, disability pension, or legal-aid application preparation. Never say NyayaSetu issues or approves a certificate.

## Ambiguity Rules

- If a message asks both case status and bail, choose `bail_enquiry` when release from custody is the main request.
- If a message mentions a lawyer only as missing evidence for bail, choose `bail_enquiry`, not `legal_rights`.
- If a user asks for a caste certificate to obtain legal aid, choose the immediate requested workflow. Use `caste_certificate` if they need that application first.
- If OCR text conflicts with user-entered text, preserve both observations and label a mismatch. Do not silently choose one.
- If evidence is not stated, mark it missing; do not infer that it exists.

## Entity Rules

- Redact names as `[NAME]`, FIR numbers as `[FIR]`, phone numbers as `[PHONE]`, and full identity numbers as `[ID]` before dataset storage.
- Aadhaar and bank values may retain only the last four digits when necessary for a correction task.
- Normalize custody duration to months only when the source unit is explicit.
- Preserve legal sections exactly, including suffixes such as `498A`.

## Urgency Rules

- `emergency`: immediate physical danger, ongoing violence, child safety, current financial fraud where freezing may still help, or medical emergency.
- `high`: custody, arrest, imminent hearing/deadline, police refusal in a serious matter, or serious benefit interruption.
- `medium`: unpaid wages, eviction pressure, application mismatch, pending legal notice, or incomplete court/civic documents.
- `low`: general information or preventive document preparation without an imminent deadline.

## Quality Acceptance

A row is accepted only when:

- module and intent are supported by the text;
- no unsupported entity is invented;
- missing-document labels distinguish mandatory from conditional evidence;
- response names the authorised route;
- response contains no guaranteed legal or government outcome;
- personal data is redacted;
- JSON conforms to `model/nyayasetu_model_contract.json`.

## Two-Reviewer Consensus

Benchmark rows require two independent reviews. Resolve disagreement through discussion or a third adjudicator. Record actual agreement; never estimate or invent it.
