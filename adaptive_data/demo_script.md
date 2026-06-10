# Live Hackathon Demo Script

## Goal
Show that NyayaSetu is not a static chatbot. It is an adaptive legal-access data system that learns from every citizen interaction.

## Flow
1. Open the NyayaSetu dashboard and show live multilingual request feed.
2. Enter Marathi query: "maza dada jail madhe ahe section 379 bail milel ka 3 mahine zale".
3. Show the system initially predicts the language incorrectly as Hindi or unknown.
4. Submit correction: language = Marathi, intent = bail_enquiry.
5. Show the dataset row updating with feedback_type = wrong_language and correction.field = language.
6. Show confidence_before = 0.38 and confidence_after = 0.92.
7. Generate bail eligibility result and document-ready output.
8. Open language_statistics.csv and adaptation_metrics.json.
9. Show Adaptive Data export and Hugging Face dataset.
10. Close with: "The system becomes more useful after every family message, every correction, and every regional-language example."

## Judge Talking Points
- Continuous learning is visible, not hidden.
- Human corrections are structured, auditable, and reusable.
- Low-resource languages are tracked separately.
- The same pipeline powers product UX, dataset quality, and model improvement.
