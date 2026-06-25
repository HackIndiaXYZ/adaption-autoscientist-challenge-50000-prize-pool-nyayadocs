---
license: mit
base_model: meta-llama/Llama-4-Scout-17B-16E-Instruct
library_name: peft
tags:
  - legal-aid
  - civic-tech
  - india
  - multilingual
  - lora
  - autoscientist
  - adaption
datasets:
  - Ananya80/nyayasetu-legal-dialogues-multilingual
language:
  - en
  - hi
  - bn
  - ta
  - te
  - mr
---

# adaption_nyayasetu_legal_assist

`adaption_nyayasetu_legal_assist` is a LoRA-adapted legal-access model trained with Adaption AutoScientist for NyayaSetu + ZamanatAI + CivicDocs. It is designed to convert multilingual citizen messages into structured legal/civic workflows: legal-aid intake, bail/surety support, missing-document detection, OCR-assisted CivicDocs preparation, and safety-boundary-aware responses.

Generated content is **not legal advice** and must be verified by a lawyer, court, government authority, or qualified legal-aid provider.

## Base Model

- Base model: `meta-llama/Llama-4-Scout-17B-16E-Instruct`
- Adapted model: `adaption_nyayasetu_legal_assist`
- Training method: supervised fine-tuning (`sft`)
- Adapter type: LoRA
- Data format: chat
- AutoScientist experiment ID: `f120ba55-a11a-4621-89a8-12e924e7766f`
- Fine-tune job ID: `8ec11627-6dd4-48ee-b4d9-0fe83c25bd8e`

## Dataset

Training data comes from the open NyayaSetu dataset:

- Hugging Face: `Ananya80/nyayasetu-legal-dialogues-multilingual`
- Kaggle: `ananyadaitkar/adaption-nyay-177c8907-3193-49c1-b337-32d744f4b2e2`

The unified dataset contains:

- 2,573 records
- 973 NyayaSetu Legal Aid records
- 670 ZamanatAI records
- 930 CivicDocs records
- 122 live Twilio webhook observations from the deployed WhatsApp pipeline
- Missing-document labels, safety boundaries, structured outputs, OCR tasks, and benchmark artifacts

## AutoScientist Results

Adaption AutoScientist reported the following improvements:

| Metric | Before | After |
|---|---:|---:|
| Dataset quality | 9.0 | 9.4 |
| Grade | B | A |
| Percentile | 41.4 | 57.7 |
| Dataset win rate | 31 | 69 |
| Legal category win rate | 35 | 66 |

Training loss decreased during the run and the adapted model outperformed the base model in the Adaption win-rate evaluation shown in the project evidence screenshots.

## Intended Use

The model is intended for civic-tech and legal-aid workflows:

- classify legal/civic issue type;
- identify missing information and missing evidence;
- structure bail/surety workflow data;
- prepare draft legal-aid and CivicDocs application guidance;
- preserve explicit legal safety boundaries;
- route users to lawyers, courts, DLSA/SLSA, police, cybercrime helpline, or authorised government offices.

## Out Of Scope

The model must not be used to:

- guarantee bail, acquittal, certificate approval, pension approval, refund, or any legal outcome;
- replace a lawyer or authorised public official;
- generate forged or altered government documents;
- store unnecessary sensitive identity data;
- provide emergency response as a substitute for police, medical, or safety services.

## Training Hyperparameters

See [`training_config.json`](./training_config.json).

Key values:

- LoRA rank: `32`
- LoRA alpha: `64`
- LoRA dropout: `0.05`
- Epochs: `3`
- Learning rate: `0.00015`
- Scheduler: cosine
- Trainable modules: all linear layers

## Evaluation Notes

Local fixed-rule baseline metrics are included in:

```text
evaluation/baseline_metrics.json
```

AutoScientist platform evidence is included in:

```text
submission_evidence/adaption/
```

Human-review status is currently:

```text
automated_review_complete_pending_human_spotcheck
```

Automated audit rows should not be described as independent human consensus until real human reviewers replace the automated reviewer labels.

## Release Status

This folder contains the public model card and training configuration. The LoRA adapter weights must be exported from Adaption and placed in this folder before publishing a complete model-weight release.

Expected weight files after export may include:

```text
adapter_config.json
adapter_model.safetensors
tokenizer_config.json
special_tokens_map.json
```

