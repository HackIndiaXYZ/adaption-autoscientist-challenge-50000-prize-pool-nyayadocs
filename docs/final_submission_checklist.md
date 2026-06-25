# Final Submission Checklist

## Completed

- Live frontend: https://nyayasetu-zamanatai.vercel.app
- Live backend health: https://nyayasetu-backend-production-2101.up.railway.app/health
- GitHub submission repo: https://github.com/HackIndiaXYZ/adaption-autoscientist-challenge-50000-prize-pool-nyayadocs
- Hugging Face dataset: https://huggingface.co/datasets/Ananya80/nyayasetu-legal-dialogues-multilingual
- Kaggle dataset: https://www.kaggle.com/datasets/ananyadaitkar/adaption-nyay-177c8907-3193-49c1-b337-32d744f4b2e2
- Adaptive Data dataset created on Adaption
- AutoScientist training completed
- LoRA training configuration documented
- Evidence screenshots saved in `submission_evidence/adaption/`

## AutoScientist Evidence

- Base model: `meta-llama/Llama-4-Scout-17B-16E-Instruct`
- Trained model: `adaption_nyayasetu_legal_assist`
- Fine-tune job ID: `8ec11627-6dd4-48ee-b4d9-0fe83c25bd8e`
- Training experiment ID: `f120ba55-a11a-4621-89a8-12e924e7766f`
- Training method: SFT LoRA
- Quality improvement: `9.0 -> 9.4`
- Grade improvement: `B -> A`
- Percentile improvement: `41.4 -> 57.7`
- Dataset win rate: `31 -> 69`
- Legal-category win rate: `35 -> 66`

## Must Do Before Final Submission

1. Export model weights from Adaption.
2. Place exported weights inside:

```text
model/adaption_nyayasetu_legal_assist/
```

Expected files may include:

```text
adapter_config.json
adapter_model.safetensors
tokenizer_config.json
special_tokens_map.json
```

3. Upload model to Hugging Face:

```bash
python3 upload_model.py
```

4. Add the final Hugging Face model link to this checklist and the README.
5. Post on LinkedIn and X:

```text
We built NyayaSetu + ZamanatAI + CivicDocs for the Adaption AutoScientist Challenge.

It turns WhatsApp/web legal and civic messages into structured justice workflows: legal-aid routing, bail/surety document support, OCR-assisted CivicDocs preparation, missing-evidence detection, and safe next steps.

Using Adaption Adaptive Data + AutoScientist, our adapted Llama-4 Scout LoRA model improved dataset win rate from 31 to 69 and legal-category win rate from 35 to 66, with dataset quality improving from 9.0 to 9.4.

Live demo: https://nyayasetu-zamanatai.vercel.app
GitHub: https://github.com/HackIndiaXYZ/adaption-autoscientist-challenge-50000-prize-pool-nyayadocs
Dataset: https://huggingface.co/datasets/Ananya80/nyayasetu-legal-dialogues-multilingual

@adaption_ai
```

6. Submit Part 1 form:

```text
https://share.hsforms.com/2r5RTDl9lSrqTQmqhRhEsQwuc9yb
```

## Claim Carefully

Safe claim:

```text
We completed an AutoScientist SFT LoRA run with measurable platform-reported improvement: dataset win rate increased from 31 to 69, legal-category win rate from 35 to 66, quality from 9.0 to 9.4, and grade from B to A.
```

Do not claim:

```text
The model gives legal advice.
The model guarantees bail/certificates.
The automated audit is independent human review.
```

